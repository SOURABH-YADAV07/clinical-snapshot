from fastapi import APIRouter, HTTPException

from app.models.summary import PatientListItem, PatientSummaryResponse
from app.services.loader import load_fhir_bundle
from app.services.normalizer import build_patient_summary, list_patients

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[PatientListItem])
def get_patients() -> list[PatientListItem]:
    return list_patients(load_fhir_bundle())


@router.get("/{patient_id}/summary", response_model=PatientSummaryResponse)
def get_patient_summary(patient_id: str) -> PatientSummaryResponse:
    summary = build_patient_summary(load_fhir_bundle(), patient_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return summary
