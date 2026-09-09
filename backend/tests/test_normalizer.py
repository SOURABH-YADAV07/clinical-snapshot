import copy
import json
from pathlib import Path

import pytest

from app.services.normalizer import build_patient_summary, list_patients

# Loaded directly from the known original file, not via load_fhir_bundle()
# (which merges everything currently in raw_data/, including any real
# uploads made through the app) — these tests assert specifics of that one
# known dataset and must not be affected by unrelated uploaded data.
_ORIGINAL_BUNDLE_PATH = (
    Path(__file__).resolve().parents[2] / "raw_data" / "scenario1_fhir_bundle[78].json"
)


@pytest.fixture(scope="module")
def bundle():
    with _ORIGINAL_BUNDLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="module")
def summary(bundle):
    return build_patient_summary(bundle, "patient-001")


def test_list_patients_marks_canonical_and_duplicate(bundle):
    items = list_patients(bundle)
    assert [item.id for item in items] == ["patient-001", "patient-002"]
    assert items[0].is_canonical is True
    assert items[0].note is None
    assert items[0].phone == "555-014-2231"
    assert items[1].is_canonical is False
    assert items[1].note is not None
    assert items[1].phone == "555-014-9987"


def test_non_canonical_patient_summary_still_works(bundle):
    duplicate_summary = build_patient_summary(bundle, "patient-002")
    assert duplicate_summary is not None
    assert duplicate_summary.patient.id == "patient-002"
    assert len(duplicate_summary.medications) == 1
    assert duplicate_summary.medications[0].id == "medicationrequest-003"


def by_id(items, resource_id):
    return next((item for item in items if item.id == resource_id), None)


def test_unknown_patient_returns_none(bundle):
    assert build_patient_summary(bundle, "patient-does-not-exist") is None


def test_canonical_patient_demographics(summary):
    assert summary.patient.id == "patient-001"
    assert summary.patient.name == "Dorothy M Whitfield"
    assert summary.patient.birth_date == "1958-03-12"


def test_us_core_race_and_ethnicity_extracted(summary):
    assert summary.patient.race == "White"
    assert summary.patient.ethnicity == "Not Hispanic or Latino"


def test_us_core_extension_absent_yields_none_not_a_crash(bundle):
    duplicate_summary = build_patient_summary(bundle, "patient-002")
    assert duplicate_summary.patient.race is None
    assert duplicate_summary.patient.ethnicity is None


def test_entered_in_error_encounter_excluded(summary):
    assert by_id(summary.encounters, "encounter-002") is None


def test_finished_encounter_included(summary):
    enc = by_id(summary.encounters, "encounter-001")
    assert enc is not None
    assert enc.status == "finished"


def test_entered_in_error_condition_excluded(summary):
    assert by_id(summary.problems, "condition-002") is None


def test_active_confirmed_condition_included_and_resolved(summary):
    cond = by_id(summary.problems, "condition-001")
    assert cond is not None
    assert cond.reference_resolved is True
    assert cond.encounter is not None
    assert cond.encounter.id == "encounter-001"


def test_condition_with_unresolved_encounter_retained_with_uncertainty(summary):
    cond = by_id(summary.problems, "condition-003")
    assert cond is not None
    assert cond.reference_resolved is False
    assert cond.encounter is None
    assert cond.encounter_reference == "Encounter/encounter-099"
    assert any("could not be resolved" in note for note in cond.uncertainty_notes)


def test_partial_date_precision_preserved(summary):
    cond = by_id(summary.problems, "condition-003")
    assert cond.onset == "2019"
    obs = by_id(summary.observations, "observation-002")
    assert obs.effective == "2020"


def test_stopped_medication_excluded(summary):
    assert by_id(summary.medications, "medicationrequest-002") is None


def test_active_medication_included(summary):
    med = by_id(summary.medications, "medicationrequest-001")
    assert med is not None
    assert med.medication.display == "Lisinopril 10 MG Oral Tablet"


def test_non_canonical_patient_medication_not_attributed(summary):
    assert by_id(summary.medications, "medicationrequest-003") is None
    flags = [f for f in summary.data_quality if f.resource_id == "medicationrequest-003"]
    assert len(flags) == 1
    assert "patient-002" in flags[0].message


def test_entered_in_error_allergy_excluded(summary):
    assert by_id(summary.allergies, "allergyintolerance-002") is None


def test_confirmed_allergy_included_with_coding_flagged(summary):
    allergy = by_id(summary.allergies, "allergyintolerance-001")
    assert allergy is not None
    assert allergy.code.display == "Penicillin"
    assert any("not SNOMED-shaped" in note for note in allergy.uncertainty_notes)
    flags = [f for f in summary.data_quality if f.resource_id == "allergyintolerance-001"]
    assert any("mismatch" in f.message for f in flags)


def test_unconfirmed_allergy_retained_with_visible_uncertainty(summary):
    allergy = by_id(summary.allergies, "allergyintolerance-003")
    assert allergy is not None
    assert allergy.verification_status == "unconfirmed"
    assert any("unconfirmed" in note for note in allergy.uncertainty_notes)


def test_missing_coding_display_not_invented(summary):
    allergy = by_id(summary.allergies, "allergyintolerance-003")
    assert allergy.code.display is None
    assert allergy.code.display_available is False

    obs = by_id(summary.observations, "observation-002")
    assert obs.code.display is None
    assert obs.code.display_available is False


def test_entered_in_error_observation_excluded(summary):
    assert by_id(summary.observations, "observation-004") is None


def test_observation_with_components_produces_multiple_values(summary):
    obs = by_id(summary.observations, "observation-001")
    assert obs is not None
    assert len(obs.values) == 2
    labels = {v.code.display for v in obs.values}
    assert labels == {"Systolic blood pressure", "Diastolic blood pressure"}


def test_unresolved_performer_reference_flagged_without_crashing(summary):
    obs = by_id(summary.observations, "observation-003")
    assert obs is not None
    flags = [f for f in summary.data_quality if f.resource_id == "observation-003"]
    assert any("practitioner-999" in f.message for f in flags)


def test_suspected_midnight_precision_flagged(summary):
    cond = by_id(summary.problems, "condition-001")
    assert any("midnight UTC" in note for note in cond.uncertainty_notes)


def _find_resource(bundle, resource_type, resource_id):
    for entry in bundle["entry"]:
        resource = entry["resource"]
        if resource["resourceType"] == resource_type and resource["id"] == resource_id:
            return resource
    raise AssertionError(f"{resource_type}/{resource_id} not found in bundle")


def test_item_moves_out_of_uncertain_once_underlying_data_is_complete(bundle):
    # condition-003 is uncertain today only because two facts are true of the
    # raw data: its code has no display, and it references an Encounter that
    # doesn't exist. This proves the normalizer (and therefore the frontend's
    # known/uncertain split, which reads these same two fields) is driven
    # entirely by those facts, not by a hardcoded resource id. Supply both
    # missing facts on an in-memory copy — raw_data/ itself is never touched
    # — and the item should come back fully resolved.
    original = by_id(build_patient_summary(bundle, "patient-001").problems, "condition-003")
    assert original.code.display_available is False
    assert original.reference_resolved is False

    improved_bundle = copy.deepcopy(bundle)
    condition = _find_resource(improved_bundle, "Condition", "condition-003")
    condition["code"]["coding"][0]["display"] = "Type 2 diabetes mellitus without complications"
    improved_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:encounter-099",
            "resource": {
                "resourceType": "Encounter",
                "id": "encounter-099",
                "status": "finished",
                "subject": {"reference": "Patient/patient-001"},
                "period": {"start": "2019-03-01T09:00:00Z", "end": "2019-03-01T09:30:00Z"},
            },
        }
    )

    improved = by_id(build_patient_summary(improved_bundle, "patient-001").problems, "condition-003")
    assert improved.code.display_available is True
    assert improved.code.display == "Type 2 diabetes mellitus without complications"
    assert improved.reference_resolved is True
    assert improved.encounter is not None
    assert improved.encounter.id == "encounter-099"

    # This is the exact predicate the frontend uses (isProblemUncertain in
    # Problems.tsx) to decide known vs. Data Quality placement.
    def is_problem_uncertain(problem):
        return not problem.code.display_available or not problem.reference_resolved

    assert is_problem_uncertain(original) is True
    assert is_problem_uncertain(improved) is False


def test_malformed_resource_is_skipped_without_crashing(bundle):
    # Relevant once bundles can be uploaded by users rather than only the
    # known-good demo file: a single bad resource must not take down the
    # whole request.
    broken_bundle = copy.deepcopy(bundle)
    broken_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:condition-broken",
            "resource": {
                "resourceType": "Condition",
                # Missing required "id" — this resource cannot validate.
                "subject": {"reference": "Patient/patient-001"},
            },
        }
    )

    summary = build_patient_summary(broken_bundle, "patient-001")

    assert summary is not None
    assert len(summary.problems) == 2


def test_unrelated_uploaded_patient_is_not_flagged_as_duplicate(bundle):
    # Regression test: a third, entirely unrelated patient (as would appear
    # after uploading a new bundle — see services/loader.py) must not be
    # mistaken for a duplicate of the canonical patient just because it
    # isn't patient-001. Only patient-002 is a documented, human-reviewed
    # duplicate.
    multi_patient_bundle = copy.deepcopy(bundle)
    multi_patient_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:patient-999",
            "resource": {
                "resourceType": "Patient",
                "id": "patient-999",
                "name": [{"family": "Rivera", "given": ["Marcus"]}],
                "birthDate": "1990-05-14",
            },
        }
    )
    multi_patient_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:medicationrequest-999",
            "resource": {
                "resourceType": "MedicationRequest",
                "id": "medicationrequest-999",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "999999"}]
                },
                "subject": {"reference": "Patient/patient-999"},
            },
        }
    )

    listed = by_id(list_patients(multi_patient_bundle), "patient-999")
    assert listed.is_canonical is True
    assert listed.note is None

    summary = build_patient_summary(multi_patient_bundle, "patient-001")
    assert not any(f.resource_id == "medicationrequest-999" for f in summary.data_quality)


def test_encounters_are_scoped_to_the_requested_patient(bundle):
    # Regression test: found by manually uploading a multi-patient bundle
    # and inspecting the response. `visible_encounters` used to be built
    # from every Encounter in the whole (now merged, multi-file) bundle,
    # filtered only by status — never by which patient it belonged to. With
    # a single-patient demo bundle this was invisible; with more than one
    # patient's encounters in the dataset, every patient's summary showed
    # every other patient's encounters too.
    other_patient_bundle = copy.deepcopy(bundle)
    other_patient_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:patient-888",
            "resource": {"resourceType": "Patient", "id": "patient-888", "name": [{"family": "Nguyen"}]},
        }
    )
    other_patient_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:encounter-888",
            "resource": {
                "resourceType": "Encounter",
                "id": "encounter-888",
                "status": "finished",
                "subject": {"reference": "Patient/patient-888"},
                "period": {"start": "2026-01-01T10:00:00Z", "end": "2026-01-01T10:30:00Z"},
            },
        }
    )
    other_patient_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:condition-888",
            "resource": {
                "resourceType": "Condition",
                "id": "condition-888",
                "clinicalStatus": {"coding": [{"code": "active"}]},
                "verificationStatus": {"coding": [{"code": "confirmed"}]},
                "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "Z00.00"}]},
                "subject": {"reference": "Patient/patient-888"},
                # References patient-001's own encounter, not one of its own —
                # this must NOT resolve, even though that encounter exists in
                # the bundle, because it belongs to a different patient.
                "encounter": {"reference": "Encounter/encounter-001"},
            },
        }
    )

    patient_001_summary = build_patient_summary(other_patient_bundle, "patient-001")
    assert all(e.id != "encounter-888" for e in patient_001_summary.encounters)

    patient_888_summary = build_patient_summary(other_patient_bundle, "patient-888")
    assert [e.id for e in patient_888_summary.encounters] == ["encounter-888"]

    condition_888 = by_id(patient_888_summary.problems, "condition-888")
    assert condition_888.reference_resolved is False
    assert condition_888.encounter is None


def test_a_second_known_duplicate_pair_works_independently_of_the_first(bundle):
    # KNOWN_DUPLICATE_PATIENT_IDS supports patient-216 -> patient-201 as a
    # second documented pair (see normalizer.py), alongside the original
    # patient-002 -> patient-001. Prove the two pairs don't interfere: each
    # canonical patient only ever sees flags for *its own* duplicate, not
    # the other pair's.
    two_pairs_bundle = copy.deepcopy(bundle)
    two_pairs_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:patient-201",
            "resource": {
                "resourceType": "Patient",
                "id": "patient-201",
                "name": [{"family": "Alvarez", "given": ["Sofia"]}],
                "birthDate": "1982-03-09",
            },
        }
    )
    two_pairs_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:patient-216",
            "resource": {
                "resourceType": "Patient",
                "id": "patient-216",
                "name": [{"family": "Alvarez", "given": ["Sofia"]}],
                "birthDate": "1982",
            },
        }
    )
    two_pairs_bundle["entry"].append(
        {
            "fullUrl": "urn:uuid:medicationrequest-216",
            "resource": {
                "resourceType": "MedicationRequest",
                "id": "medicationrequest-216",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "111111"}]
                },
                "subject": {"reference": "Patient/patient-216"},
            },
        }
    )

    listed = {item.id: item for item in list_patients(two_pairs_bundle)}
    assert listed["patient-201"].is_canonical is True
    assert listed["patient-216"].is_canonical is False
    assert "patient-201" in listed["patient-216"].note
    # The original pair is unaffected by the new one existing.
    assert listed["patient-002"].is_canonical is False
    assert "patient-001" in listed["patient-002"].note

    patient_201_summary = build_patient_summary(two_pairs_bundle, "patient-201")
    assert patient_201_summary.patient.is_canonical is True
    assert patient_201_summary.patient.note is None
    assert any(f.resource_id == "medicationrequest-216" for f in patient_201_summary.data_quality)

    patient_216_summary = build_patient_summary(two_pairs_bundle, "patient-216")
    assert patient_216_summary.patient.is_canonical is False
    assert "patient-201" in patient_216_summary.patient.note

    # patient-001's own summary must not pick up patient-216's medication —
    # they belong to an unrelated canonical/duplicate pair.
    patient_001_summary = build_patient_summary(two_pairs_bundle, "patient-001")
    assert not any(f.resource_id == "medicationrequest-216" for f in patient_001_summary.data_quality)


def test_non_dict_entries_are_skipped_without_crashing():
    # Found by adversarial testing of the upload endpoint: bundle_dict.get()
    # patterns assumed every "entry" was a dict with a dict "resource"
    # inside. A garbage entry (string, number, null) in an uploaded Bundle
    # crashed the whole request with an unhandled 500 instead of being
    # skipped like any other malformed resource.
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            "not a dict",
            123,
            None,
            {"not_a_resource_key": "still garbage"},
            {"resource": "resource value is a string, not a dict"},
            {"resource": {"resourceType": "Patient", "id": "patient-ok", "name": [{"family": "Ok"}]}},
        ],
    }

    items = list_patients(bundle)

    assert [item.id for item in items] == ["patient-ok"]


def test_non_string_resource_type_or_id_is_skipped_without_crashing():
    # A second crash found the same way: resourceType or id being a list or
    # dict (instead of a string) made them unhashable, crashing the
    # _MODEL_BY_RESOURCE_TYPE dict lookup with an unhandled TypeError rather
    # than a clean skip.
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": ["Patient"], "id": "patient-bad-type"}},
            {"resource": {"resourceType": "Patient", "id": {"nested": "dict"}}},
            {"resource": {"resourceType": "Patient", "id": "patient-ok", "name": [{"family": "Ok"}]}},
        ],
    }

    items = list_patients(bundle)

    assert [item.id for item in items] == ["patient-ok"]
