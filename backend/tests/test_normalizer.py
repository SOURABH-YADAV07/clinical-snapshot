import pytest

from app.services.loader import load_fhir_bundle
from app.services.normalizer import build_patient_summary, list_patients


@pytest.fixture(scope="module")
def bundle():
    return load_fhir_bundle()


@pytest.fixture(scope="module")
def summary(bundle):
    return build_patient_summary(bundle, "patient-001")


def test_list_patients_marks_canonical_and_duplicate(bundle):
    items = list_patients(bundle)
    assert [item.id for item in items] == ["patient-001", "patient-002"]
    assert items[0].is_canonical is True
    assert items[0].note is None
    assert items[1].is_canonical is False
    assert items[1].note is not None


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
