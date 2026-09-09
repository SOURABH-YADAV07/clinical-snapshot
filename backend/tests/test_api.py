import json

from fastapi.testclient import TestClient

from app.services import loader
from app.main import app

client = TestClient(app)


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


def test_patient_summary_success():
    response = client.get("/api/patients/patient-001/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["id"] == "patient-001"
    assert len(data["problems"]) == 2
    assert len(data["medications"]) == 1
    assert len(data["data_quality"]) == 11


def test_patient_summary_not_found():
    response = client.get("/api/patients/does-not-exist/summary")
    assert response.status_code == 404


def test_list_patients():
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
