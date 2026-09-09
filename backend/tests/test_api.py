import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.services import loader
from app.main import app

client = TestClient(app)

_ORIGINAL_BUNDLE_PATH = (
    Path(__file__).resolve().parents[2] / "raw_data" / "scenario1_fhir_bundle[78].json"
)


def _bundle(entries):
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


def _patient_entry(patient_id, family):
    return {"resource": {"resourceType": "Patient", "id": patient_id, "name": [{"family": family}]}}


def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def _isolate_to_original_bundle(tmp_path, monkeypatch):
    # Shared by tests that assert specifics of the known original dataset —
    # must not be affected by real uploads that exist in raw_data/.
    shutil.copy(_ORIGINAL_BUNDLE_PATH, tmp_path / _ORIGINAL_BUNDLE_PATH.name)
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)


def test_patient_summary_success(tmp_path, monkeypatch):
    _isolate_to_original_bundle(tmp_path, monkeypatch)
    response = client.get("/api/patients/patient-001/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["id"] == "patient-001"
    assert len(data["problems"]) == 2
    assert len(data["medications"]) == 1
    assert len(data["data_quality"]) == 11


def test_patient_summary_not_found(tmp_path, monkeypatch):
    _isolate_to_original_bundle(tmp_path, monkeypatch)
    response = client.get("/api/patients/does-not-exist/summary")
    assert response.status_code == 404


def test_list_patients(tmp_path, monkeypatch):
    _isolate_to_original_bundle(tmp_path, monkeypatch)
    response = client.get("/api/patients")
    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == ["patient-001", "patient-002"]

    canonical = data[0]
    assert canonical["is_canonical"] is True
    assert canonical["note"] is None

    duplicate = data[1]
    assert duplicate["is_canonical"] is False
    assert duplicate["note"] is not None


def test_cors_allows_frontend_origin():
    response = client.options(
        "/api/patients/patient-001/summary",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_upload_bundle_success(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    bundle = _bundle([_patient_entry("patient-new", "Newcomer")])

    response = client.post("/api/bundles", json=bundle)

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == ["patient-new"]
    saved_files = list(tmp_path.glob("uploaded-*.json"))
    assert len(saved_files) == 1
    assert json.loads(saved_files[0].read_text(encoding="utf-8")) == bundle


def test_upload_bundle_rejects_non_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    response = client.post("/api/bundles", json={"resourceType": "Patient", "id": "x"})
    assert response.status_code == 422
    assert not list(tmp_path.glob("*.json"))


def test_upload_bundle_rejects_missing_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    response = client.post("/api/bundles", json={"resourceType": "Bundle"})
    assert response.status_code == 422
    assert not list(tmp_path.glob("*.json"))


def test_upload_bundle_rejects_no_patients(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    bundle = _bundle([{"resource": {"resourceType": "Observation", "id": "obs-1", "status": "final"}}])
    response = client.post("/api/bundles", json=bundle)
    assert response.status_code == 422
    assert not list(tmp_path.glob("*.json"))


def test_uploaded_bundle_appears_in_merged_patient_list(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    (tmp_path / "seed.json").write_text(
        json.dumps(_bundle([_patient_entry("patient-seed", "Seed")])), encoding="utf-8"
    )

    upload_response = client.post("/api/bundles", json=_bundle([_patient_entry("patient-uploaded", "Uploaded")]))
    assert upload_response.status_code == 200

    list_response = client.get("/api/patients")
    assert list_response.status_code == 200
    ids = {item["id"] for item in list_response.json()}
    assert ids == {"patient-seed", "patient-uploaded"}


def test_empty_raw_data_returns_clean_503_not_a_raw_500(tmp_path, monkeypatch):
    # raw_data/ with no .json files at all (fresh checkout, demo file
    # removed) used to produce an unhandled 500 with no detail.
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)

    list_response = client.get("/api/patients")
    assert list_response.status_code == 503
    assert "raw_data" in list_response.json()["detail"]

    summary_response = client.get("/api/patients/patient-001/summary")
    assert summary_response.status_code == 503


def test_storage_write_failure_returns_clean_503_not_a_raw_500(tmp_path, monkeypatch):
    # A disk write failure while saving an upload (permission denied, full
    # disk, read-only filesystem) used to reach the client as an unhandled
    # 500 with no detail. Uses a mock path object, never the real
    # RAW_DATA_DIR, so the failure is guaranteed before any real I/O.
    fake_dir = MagicMock()
    fake_dir.mkdir.side_effect = PermissionError("Permission denied")
    monkeypatch.setattr(loader, "RAW_DATA_DIR", fake_dir)
    bundle = _bundle([_patient_entry("patient-x", "X")])

    response = client.post("/api/bundles", json=bundle)

    assert response.status_code == 503
    assert "storage error" in response.json()["detail"].lower()


def test_unexpected_error_returns_clean_500_not_a_raw_response(monkeypatch):
    # Last-resort safety net: any genuinely unexpected exception type must
    # still produce a structured JSON response, not Starlette's bare
    # "Internal Server Error" text with no body. Needs a client with
    # raise_server_exceptions=False: TestClient's default re-raises
    # exceptions only caught by a blanket Exception handler (by design, so
    # test suites still surface real bugs) — this test wants to see what an
    # actual client would receive, not that test-time protection.
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("something totally unexpected")

    monkeypatch.setattr("app.api.patients.build_patient_summary", _raise_runtime_error)

    lenient_client = TestClient(app, raise_server_exceptions=False)
    response = lenient_client.get("/api/patients/patient-001/summary")

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
