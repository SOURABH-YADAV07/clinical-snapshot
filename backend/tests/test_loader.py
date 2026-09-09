import json

import pytest

from app.services import loader


def _write_bundle(path, timestamp, entries):
    path.write_text(
        json.dumps({"resourceType": "Bundle", "type": "collection", "timestamp": timestamp, "entry": entries}),
        encoding="utf-8",
    )


def _patient_entry(patient_id, family):
    return {
        "resource": {
            "resourceType": "Patient",
            "id": patient_id,
            "name": [{"family": family, "given": ["Test"]}],
        }
    }


def test_load_fhir_bundle_merges_multiple_files(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    _write_bundle(tmp_path / "a.json", "2020-01-01T00:00:00Z", [_patient_entry("patient-a", "Alpha")])
    _write_bundle(tmp_path / "b.json", "2021-06-01T00:00:00Z", [_patient_entry("patient-b", "Beta")])

    merged = loader.load_fhir_bundle()

    ids = {entry["resource"]["id"] for entry in merged["entry"]}
    assert ids == {"patient-a", "patient-b"}
    assert merged["timestamp"] == "2021-06-01T00:00:00Z"


def test_load_fhir_bundle_first_file_wins_on_duplicate_id(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    _write_bundle(tmp_path / "a.json", "2020-01-01T00:00:00Z", [_patient_entry("patient-x", "First")])
    _write_bundle(tmp_path / "b.json", "2021-01-01T00:00:00Z", [_patient_entry("patient-x", "Second")])

    merged = loader.load_fhir_bundle()

    matching = [e for e in merged["entry"] if e["resource"]["id"] == "patient-x"]
    assert len(matching) == 1
    assert matching[0]["resource"]["name"][0]["family"] == "First"


def test_load_fhir_bundle_raises_when_directory_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        loader.load_fhir_bundle()


def test_save_bundle_file_writes_readable_json(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    bundle = {"resourceType": "Bundle", "type": "collection", "entry": [_patient_entry("patient-z", "Zed")]}

    path = loader.save_bundle_file(bundle)

    assert path.parent == tmp_path
    assert path.name.startswith("uploaded-")
    assert json.loads(path.read_text(encoding="utf-8")) == bundle


def test_load_fhir_bundle_skips_files_that_are_not_bundle_shaped(tmp_path, monkeypatch):
    # A file could end up in raw_data/ that parses as valid JSON but isn't a
    # Bundle at all (a bare array, a string, an object with no "entry").
    # These must be skipped and logged, not crash every request that lists
    # or summarizes patients.
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    _write_bundle(tmp_path / "good.json", "2022-01-01T00:00:00Z", [_patient_entry("patient-good", "Good")])
    (tmp_path / "array.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    (tmp_path / "string.json").write_text(json.dumps("just a string"), encoding="utf-8")
    (tmp_path / "no_entry.json").write_text(json.dumps({"resourceType": "Bundle"}), encoding="utf-8")

    merged = loader.load_fhir_bundle()

    ids = {entry["resource"]["id"] for entry in merged["entry"]}
    assert ids == {"patient-good"}


def test_load_fhir_bundle_skips_entries_with_unhashable_resource_type_or_id(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "RAW_DATA_DIR", tmp_path)
    _write_bundle(
        tmp_path / "mixed.json",
        "2022-01-01T00:00:00Z",
        [
            {"resource": {"resourceType": ["Patient"], "id": "patient-bad-type"}},
            {"resource": {"resourceType": "Patient", "id": {"nested": "dict"}}},
            *[_patient_entry("patient-good", "Good")],
        ],
    )

    merged = loader.load_fhir_bundle()

    ids = {entry["resource"]["id"] for entry in merged["entry"]}
    assert ids == {"patient-good"}
