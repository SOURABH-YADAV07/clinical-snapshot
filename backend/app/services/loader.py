"""Reads and merges FHIR Bundle files from raw_data/, and saves uploads there.
Every file is treated as untrusted input, not just uploads — malformed files
or resources are skipped and logged, never allowed to crash a request."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parents[3] / "raw_data"


def load_fhir_bundle() -> dict[str, Any]:
    """Load and merge every Bundle JSON file in raw_data/ into one combined Bundle.

    Files are read in filename order for deterministic behavior. If two files
    define the same resource (same resourceType + id), the first one loaded
    wins and the collision is logged — never silently overwritten.
    """
    bundle_files = sorted(RAW_DATA_DIR.glob("*.json"))
    if not bundle_files:
        raise FileNotFoundError(f"No bundle files found in {RAW_DATA_DIR}")

    merged_entries: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], str] = {}
    latest_timestamp: str | None = None

    for path in bundle_files:
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Skipping unreadable bundle file %s: %s", path.name, error)
            continue

        if not isinstance(data, dict) or not isinstance(data.get("entry"), list):
            logger.warning("Skipping %s: not a well-formed Bundle (missing/invalid 'entry')", path.name)
            continue

        for entry in data["entry"]:
            if not isinstance(entry, dict):
                continue
            resource = entry.get("resource")
            if not isinstance(resource, dict):
                continue
            resource_type, resource_id = resource.get("resourceType"), resource.get("id")
            if not isinstance(resource_type, str) or not isinstance(resource_id, str):
                continue
            key = (resource_type, resource_id)
            if key in seen:
                logger.warning(
                    "Duplicate resource %s/%s in %s ignored (already loaded from %s)",
                    key[0],
                    key[1],
                    path.name,
                    seen[key],
                )
                continue
            seen[key] = path.name
            merged_entries.append(entry)

        timestamp = data.get("timestamp")
        if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
            latest_timestamp = timestamp

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": latest_timestamp,
        "entry": merged_entries,
    }


def save_bundle_file(bundle: dict[str, Any]) -> Path:
    """Save an uploaded Bundle as a new file in raw_data/. Never overwrites existing files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DATA_DIR / f"uploaded-{uuid.uuid4().hex[:12]}.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(bundle, file, indent=2)
    return path
