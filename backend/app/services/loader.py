import json
from pathlib import Path
from typing import Any


BUNDLE_PATH = (
    Path(__file__).resolve().parents[3]
    / "raw_data"
    / "scenario1_fhir_bundle[78].json"
)


def load_fhir_bundle() -> dict[str, Any]:
    """Load the raw FHIR Bundle from the project's raw_data directory."""
    with BUNDLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)