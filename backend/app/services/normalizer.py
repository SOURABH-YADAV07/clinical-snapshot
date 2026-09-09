import re
from datetime import datetime
from typing import Any

from app.models.fhir import (
    FHIRAllergyIntolerance,
    FHIRCodeableConcept,
    FHIRCondition,
    FHIREncounter,
    FHIRMedicationRequest,
    FHIRObservation,
    FHIRPatient,
    FHIRReference,
)
from app.models.summary import (
    AllergySummary,
    CodeDisplay,
    DataQualityFlag,
    EncounterSummary,
    MedicationSummary,
    ObservationSummary,
    ObservationValue,
    PatientListItem,
    PatientSummary,
    PatientSummaryResponse,
    ProblemSummary,
)

# Documented assumption (see docs/README.md, "Resolved Decisions" #1):
# patient-001 is treated as canonical because clinical resources reference it
# and it carries richer demographics. patient-002 is never merged into it.
CANONICAL_PATIENT_ID = "patient-001"

_MIDNIGHT_UTC_RE = re.compile(r"T00:00:00Z$")
_SNOMED_SHAPE_RE = re.compile(r"^\d{6,18}$")

_MODEL_BY_RESOURCE_TYPE = {
    "Patient": FHIRPatient,
    "Encounter": FHIREncounter,
    "Condition": FHIRCondition,
    "Observation": FHIRObservation,
    "MedicationRequest": FHIRMedicationRequest,
    "AllergyIntolerance": FHIRAllergyIntolerance,
}


def build_patient_summary(bundle_dict: dict[str, Any], patient_id: str) -> PatientSummaryResponse | None:
    resources = _parse_resources(bundle_dict)
    patient = resources["Patient"].get(patient_id)
    if patient is None:
        return None

    bundle_timestamp = bundle_dict.get("timestamp")
    data_quality: list[DataQualityFlag] = []

    all_encounters = {
        eid: _build_encounter(enc, bundle_timestamp) for eid, enc in resources["Encounter"].items()
    }
    visible_encounters = [
        summary
        for eid, summary in all_encounters.items()
        if resources["Encounter"][eid].status != "entered-in-error"
    ]
    visible_encounters.sort(key=lambda e: e.start or "", reverse=True)

    problems = _build_problems(resources["Condition"], patient_id, all_encounters, data_quality)
    medications = _build_medications(resources["MedicationRequest"], patient_id)
    allergies = _build_allergies(resources["AllergyIntolerance"], patient_id, data_quality)
    observations = _build_observations(resources["Observation"], patient_id, all_encounters, data_quality)

    if patient_id == CANONICAL_PATIENT_ID:
        _flag_cross_patient_medications(resources["MedicationRequest"], data_quality)

    return PatientSummaryResponse(
        patient=_build_patient(patient),
        problems=problems,
        medications=medications,
        allergies=allergies,
        encounters=visible_encounters,
        observations=observations,
        data_quality=data_quality,
    )


def list_patients(bundle_dict: dict[str, Any]) -> list[PatientListItem]:
    resources = _parse_resources(bundle_dict)
    items = []
    for patient in resources["Patient"].values():
        built = _build_patient(patient)
        is_canonical = patient.id == CANONICAL_PATIENT_ID
        note = (
            None
            if is_canonical
            else (
                f"Not selected as the canonical record (see {CANONICAL_PATIENT_ID}); "
                "clinical resources attributed to it are not merged into the canonical summary."
            )
        )
        items.append(
            PatientListItem(
                id=built.id,
                name=built.name,
                birth_date=built.birth_date,
                is_canonical=is_canonical,
                note=note,
            )
        )
    items.sort(key=lambda item: (not item.is_canonical, item.id))
    return items


def _parse_resources(bundle_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {rt: {} for rt in _MODEL_BY_RESOURCE_TYPE}
    for entry in bundle_dict.get("entry", []):
        raw = entry.get("resource", {})
        model_cls = _MODEL_BY_RESOURCE_TYPE.get(raw.get("resourceType"))
        if model_cls is None:
            continue
        model = model_cls.model_validate(raw)
        parsed[model.resourceType][model.id] = model
    return parsed


def _code_display(cc: FHIRCodeableConcept | None) -> CodeDisplay:
    if cc is None or not cc.coding:
        return CodeDisplay(display_available=False)
    coding = cc.coding[0]
    return CodeDisplay(
        system=coding.system,
        code=coding.code,
        display=coding.display,
        display_available=coding.display is not None,
    )


def _status_code(cc: FHIRCodeableConcept | None) -> str | None:
    if cc is None or not cc.coding:
        return None
    return cc.coding[0].code


def _reference_parts(ref: FHIRReference | None) -> tuple[str, str] | None:
    if ref is None or not ref.reference or "/" not in ref.reference:
        return None
    rtype, rid = ref.reference.split("/", 1)
    return rtype, rid


def _precision_note(dt: str | None) -> str | None:
    if not dt:
        return None
    if len(dt) <= 4:
        return "Date has year-only precision."
    if _MIDNIGHT_UTC_RE.search(dt):
        return "Suspected coarser precision than stated (value falls exactly on midnight UTC)."
    return None


def _age_days(start: str | None, bundle_timestamp: str | None) -> int | None:
    if not start or not bundle_timestamp:
        return None
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        ref_dt = datetime.fromisoformat(bundle_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (ref_dt - start_dt).days


def _build_patient(patient: FHIRPatient) -> PatientSummary:
    name = None
    if patient.name:
        n = patient.name[0]
        given = " ".join(n.given) if n.given else ""
        name = " ".join(part for part in [given, n.family] if part) or None

    phone = None
    if patient.telecom:
        entry = next((t for t in patient.telecom if t.system == "phone"), patient.telecom[0])
        phone = entry.value

    address = None
    if patient.address:
        a = patient.address[0]
        line = ", ".join(a.line) if a.line else None
        city_state = ", ".join(part for part in [a.city, a.state] if part)
        city_state_zip = f"{city_state} {a.postalCode}".strip() if a.postalCode else city_state
        address = ", ".join(part for part in [line, city_state_zip] if part) or None

    return PatientSummary(
        id=patient.id,
        name=name,
        birth_date=patient.birthDate,
        gender=patient.gender,
        phone=phone,
        address=address,
    )


def _build_encounter(enc: FHIREncounter, bundle_timestamp: str | None) -> EncounterSummary:
    start = enc.period.start if enc.period else None
    end = enc.period.end if enc.period else None
    notes = [note for note in [_precision_note(start)] if note]
    return EncounterSummary(
        id=enc.id,
        type=_code_display(enc.type[0]) if enc.type else None,
        status=enc.status,
        start=start,
        end=end,
        age_days_at_snapshot=_age_days(start, bundle_timestamp),
        uncertainty_notes=notes,
    )


def _resolve_encounter_reference(
    ref: FHIRReference | None, all_encounters: dict[str, EncounterSummary]
) -> tuple[EncounterSummary | None, str | None, bool]:
    if ref is None or not ref.reference:
        return None, None, True  # no reference present, so nothing failed to resolve
    parts = _reference_parts(ref)
    resolved_summary = all_encounters.get(parts[1]) if parts and parts[0] == "Encounter" else None
    return resolved_summary, ref.reference, resolved_summary is not None


def _build_problems(
    conditions: dict[str, FHIRCondition],
    patient_id: str,
    all_encounters: dict[str, EncounterSummary],
    data_quality: list[DataQualityFlag],
) -> list[ProblemSummary]:
    results = []
    for cond in conditions.values():
        parts = _reference_parts(cond.subject)
        if parts != ("Patient", patient_id):
            continue

        clinical_status = _status_code(cond.clinicalStatus)
        verification_status = _status_code(cond.verificationStatus)
        if verification_status == "entered-in-error":
            continue
        if clinical_status not in {"active", "recurrence", "relapse"}:
            continue

        notes = [note for note in [_precision_note(cond.onsetDateTime)] if note]
        encounter_summary, encounter_reference, resolved = _resolve_encounter_reference(
            cond.encounter, all_encounters
        )
        if encounter_reference and not resolved:
            notes.append(f"Referenced encounter ({encounter_reference}) could not be resolved.")
            data_quality.append(
                DataQualityFlag(
                    message=f"Condition references {encounter_reference}, which is not present in the Bundle.",
                    resource_type="Condition",
                    resource_id=cond.id,
                )
            )

        results.append(
            ProblemSummary(
                id=cond.id,
                code=_code_display(cond.code),
                clinical_status=clinical_status,
                verification_status=verification_status,
                onset=cond.onsetDateTime,
                encounter=encounter_summary,
                encounter_reference=encounter_reference,
                reference_resolved=resolved,
                uncertainty_notes=notes,
            )
        )
    return results


def _build_medications(
    med_requests: dict[str, FHIRMedicationRequest], patient_id: str
) -> list[MedicationSummary]:
    results = []
    for med in med_requests.values():
        parts = _reference_parts(med.subject)
        if parts != ("Patient", patient_id):
            continue
        if med.status != "active":
            continue

        instructions = med.dosageInstruction[0].text if med.dosageInstruction else None
        notes = [note for note in [_precision_note(med.authoredOn)] if note]
        results.append(
            MedicationSummary(
                id=med.id,
                medication=_code_display(med.medicationCodeableConcept),
                instructions=instructions,
                authored_on=med.authoredOn,
                status=med.status,
                uncertainty_notes=notes,
            )
        )
    return results


def _flag_cross_patient_medications(
    med_requests: dict[str, FHIRMedicationRequest], data_quality: list[DataQualityFlag]
) -> None:
    for med in med_requests.values():
        parts = _reference_parts(med.subject)
        if med.status == "active" and parts and parts[0] == "Patient" and parts[1] != CANONICAL_PATIENT_ID:
            code = _code_display(med.medicationCodeableConcept)
            data_quality.append(
                DataQualityFlag(
                    message=(
                        f"Active medication (code {code.code or 'unknown'}) exists on a duplicate "
                        f"patient record ({parts[1]}) that has not been merged into the canonical "
                        "patient and is therefore not included in Active Medications."
                    ),
                    resource_type="MedicationRequest",
                    resource_id=med.id,
                )
            )


def _build_allergies(
    allergies: dict[str, FHIRAllergyIntolerance],
    patient_id: str,
    data_quality: list[DataQualityFlag],
) -> list[AllergySummary]:
    results = []
    for allergy in allergies.values():
        parts = _reference_parts(allergy.patient)
        if parts != ("Patient", patient_id):
            continue

        clinical_status = _status_code(allergy.clinicalStatus)
        verification_status = _status_code(allergy.verificationStatus)
        if verification_status == "entered-in-error":
            continue
        if clinical_status != "active":
            continue

        notes = []
        if verification_status != "confirmed":
            notes.append(f"Verification status is {verification_status or 'unknown'}.")

        code = _code_display(allergy.code)
        if (
            code.system
            and code.system.endswith("snomed.info/sct")
            and code.code
            and not _SNOMED_SHAPE_RE.match(code.code)
        ):
            notes.append(f"Coding system is SNOMED CT but code '{code.code}' is not SNOMED-shaped.")
            data_quality.append(
                DataQualityFlag(
                    message=(
                        f"AllergyIntolerance code/system mismatch: system is SNOMED CT but code "
                        f"'{code.code}' is not a well-formed SNOMED CT identifier."
                    ),
                    resource_type="AllergyIntolerance",
                    resource_id=allergy.id,
                )
            )

        if not code.display_available:
            data_quality.append(
                DataQualityFlag(
                    message=(
                        "Allergy has no coding display and cannot be verified as distinct from other "
                        "listed allergies without a terminology service."
                    ),
                    resource_type="AllergyIntolerance",
                    resource_id=allergy.id,
                )
            )

        precision_note = _precision_note(allergy.recordedDate)
        if precision_note:
            notes.append(precision_note)

        results.append(
            AllergySummary(
                id=allergy.id,
                code=code,
                clinical_status=clinical_status,
                verification_status=verification_status,
                criticality=allergy.criticality,
                uncertainty_notes=notes,
            )
        )
    return results


def _build_observations(
    observations: dict[str, FHIRObservation],
    patient_id: str,
    all_encounters: dict[str, EncounterSummary],
    data_quality: list[DataQualityFlag],
) -> list[ObservationSummary]:
    results = []
    for obs in observations.values():
        parts = _reference_parts(obs.subject)
        if parts != ("Patient", patient_id):
            continue
        if obs.status == "entered-in-error":
            continue

        notes = [note for note in [_precision_note(obs.effectiveDateTime)] if note]
        encounter_summary, encounter_reference, resolved = _resolve_encounter_reference(
            obs.encounter, all_encounters
        )
        if encounter_reference and not resolved:
            data_quality.append(
                DataQualityFlag(
                    message=f"Observation references {encounter_reference}, which is not present in the Bundle.",
                    resource_type="Observation",
                    resource_id=obs.id,
                )
            )

        for performer in obs.performer or []:
            if performer.reference:
                data_quality.append(
                    DataQualityFlag(
                        message=f"Observation references {performer.reference}, which is not present in the Bundle.",
                        resource_type="Observation",
                        resource_id=obs.id,
                    )
                )

        if obs.component:
            values = [
                ObservationValue(
                    code=_code_display(c.code),
                    value=c.valueQuantity.value if c.valueQuantity else None,
                    unit=c.valueQuantity.unit if c.valueQuantity else None,
                )
                for c in obs.component
            ]
        elif obs.valueQuantity:
            values = [ObservationValue(value=obs.valueQuantity.value, unit=obs.valueQuantity.unit)]
        else:
            values = []

        results.append(
            ObservationSummary(
                id=obs.id,
                code=_code_display(obs.code),
                values=values,
                effective=obs.effectiveDateTime,
                encounter=encounter_summary,
                encounter_reference=encounter_reference,
                reference_resolved=resolved,
                uncertainty_notes=notes,
            )
        )
    return results
