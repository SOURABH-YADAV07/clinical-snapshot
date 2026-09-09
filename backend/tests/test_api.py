from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
    assert len(data["data_quality"]) == 5


def test_patient_summary_not_found():
    response = client.get("/api/patients/does-not-exist/summary")
    assert response.status_code == 404


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
