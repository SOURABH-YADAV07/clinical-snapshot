"""Bundle upload endpoint. Validates before saving, so a rejected upload
never touches raw_data/ — only a structurally valid Bundle with at least
one Patient gets written."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.summary import PatientListItem
from app.services.loader import save_bundle_file
from app.services.normalizer import list_patients

router = APIRouter(prefix="/api/bundles", tags=["bundles"])


@router.post("", response_model=list[PatientListItem])
def upload_bundle(bundle: dict[str, Any]) -> list[PatientListItem]:
    if bundle.get("resourceType") != "Bundle":
        raise HTTPException(status_code=422, detail="Uploaded JSON must have resourceType 'Bundle'.")

    entries = bundle.get("entry")
    if not isinstance(entries, list) or len(entries) == 0:
        raise HTTPException(status_code=422, detail="Bundle must contain a non-empty 'entry' array.")

    # list_patients() itself is defensive (see normalizer.py), so a
    # malformed resource here is skipped rather than raising the 422 below.
    patients_in_upload = list_patients(bundle)
    if not patients_in_upload:
        raise HTTPException(status_code=422, detail="Bundle does not contain any Patient resources.")

    save_bundle_file(bundle)
    return patients_in_upload
