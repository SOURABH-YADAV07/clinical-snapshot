# Clinical Snapshot

A small full-stack application that ingests a synthetic FHIR R4 Bundle, normalizes and reconciles the clinical data, and presents a safe, scannable patient clinical snapshot.

## Project Overview

This project was developed as a take-home assessment for Centauri Health Solutions.

The application is designed to:

- Load the provided synthetic FHIR R4 Bundle.
- Model the required FHIR resources using Pydantic.
- Normalize and reconcile the input data.
- Handle conflicting and incomplete data conservatively.
- Exclude resources that should not be presented as current clinical facts.
- Preserve uncertainty instead of guessing or silently hiding it.
- Expose a patient-summary API using FastAPI.
- Render a one-page clinical snapshot using React, TypeScript, and Next.js.

The primary focus of the implementation is **clinical/data safety, correctness, readable code, and clear communication of uncertainty**.

---

## Assessment Data

The application uses the provided synthetic FHIR R4 Bundle:

```text
scenario1_fhir_bundle[78].json
```

The Bundle contains 17 entries and includes resources such as:

- Patient
- Encounter
- Condition
- Observation
- MedicationRequest
- AllergyIntolerance

The data intentionally contains production-like data-quality issues, including:

- Multiple Patient resources with overlapping and conflicting fields.
- Resources marked as entered-in-error or inactive.
- Missing human-readable coding display values.
- References to resources that are not present in the Bundle.
- Dates with different levels of precision.
- US Core extensions.

The data is treated as having uncertain provenance.

### Identified Data-Quality Issues

A review of the Bundle surfaced further issues beyond those listed above. They
are recorded here because they directly shape the normalization rules.

**Patient reconciliation**

- `patient-001` and `patient-002` disagree on middle initial, birth-date
  precision, MRN, phone number (value and use), and address formatting.
- Neither Patient carries `meta.lastUpdated`, so there is no recency-based way
  to arbitrate between them.
- Neither Patient carries a `Patient.link` element, which is FHIR's mechanism
  for asserting a duplicate or replaced record. The Bundle therefore contains
  no explicit assertion that the two records describe the same person.

**Cross-patient data**

- `medicationrequest-003` is an `active` medication belonging to `patient-002`,
  not to the canonical patient. It is the only clinical resource attached to
  the duplicate record.

**Unresolved references**

- `condition-003` references `Encounter/encounter-099`, which is absent.
- `observation-003` references `Practitioner/practitioner-999`, which is absent.
- No `Practitioner`, `Organization`, or `Medication` resources exist in the
  Bundle at all.
- Entries are identified by `fullUrl` values such as `urn:uuid:patient-001`,
  while all references are relative (`Patient/patient-001`). Reference
  resolution is therefore performed on resource type and id.

**Coding integrity**

- `allergyintolerance-001` declares the SNOMED CT system but carries the code
  `7980-2`, which is not a well-formed SNOMED CT identifier. The system/code
  pair is internally inconsistent even though a display value is present.
- Conditions are coded in ICD-10-CM only, with no SNOMED CT equivalent.

**Date precision**

- Several values are year-only: `2015`, `2016`, `2019`, `2020`, `2022`.
- Some timestamps fall exactly on midnight UTC (`2018-01-01T00:00:00Z`,
  `2021-06-02T00:00:00Z`), which may indicate coarser precision that was
  already inflated upstream.
- A laboratory result (`observation-002`) carries year-only precision.

**Missing elements**

- Only one of four Observations has a `category`, so relevant observations
  cannot be selected by category alone.
- No Condition has a `category`, so problem-list entries cannot be
  distinguished from encounter diagnoses.
- No Observation has a `referenceRange` or `interpretation`, so nothing in the
  data itself marks a value as abnormal.
- No MedicationRequest has a `requester`.
- `medicationrequest-002` is `stopped` with no `statusReason` and no end date.
- No AllergyIntolerance has a `type` or `category`.

**Structural conformance**

- `condition-002` and `allergyintolerance-002` both carry a `clinicalStatus`
  alongside a `verificationStatus` of `entered-in-error`. FHIR invariants
  `con-5` and `ait-2` prohibit this, so the loader must be deliberately lenient
  rather than strictly validating.
- `Bundle.total` is present on a `collection` Bundle, where it is not
  meaningful.
- The `urn:uuid:` prefixes are not RFC 4122 UUIDs.

**Privacy**

- `patient-001` carries an SSN identifier. It is partially masked, has no
  clinical value in a snapshot view, and is therefore not exposed by the API.

**Temporal consistency**

- `observation-003` is timestamped two minutes before the start of
  `encounter-001` and carries no encounter reference.
- `medicationrequest-001` is authored after `encounter-001` ends while still
  referencing it.
- `Bundle.timestamp` is later than every clinical event it contains, so
  "recent" cannot be derived from the current date.

---

## Implementation Status

This section reflects the actual state of the repository, not the intended end state.

| Area | Status |
|---|---|
| Project structure and Python environment | Complete |
| Dependency pinning (`requirements.txt`) | Complete |
| FHIR Bundle loader (`services/loader.py`) | Complete — loads all 17 entries |
| FastAPI application boots, `/docs` available | Complete |
| Input data-quality analysis | Complete — see *Identified Data-Quality Issues* |
| FHIR Pydantic models (`models/fhir.py`) | Not started |
| Summary response models (`models/summary.py`) | Not started |
| Normalizer / reconciliation (`services/normalizer.py`) | Not started |
| Patient summary endpoint (`api/patients.py`) | Not started |
| Backend tests | Not started |
| Frontend (Next.js) | Not started |

### Verified working

- `GET /` returns `200`.
- `GET /docs` returns `200` (FastAPI interactive documentation).
- The loader resolves the Bundle path independently of the current working
  directory and parses all 17 entries, matching the Bundle's declared `total`.

### Immediate next steps

1. Resolve the open normalization questions (see *Open Decisions*).
2. Implement the FHIR Pydantic models.
3. Implement the normalizer, with tests written alongside each safety rule.
4. Add the patient summary endpoint.
5. Enable CORS for the Next.js development origin, so the frontend can
   consume the API from a different port.
6. Scaffold and build the frontend snapshot.

---

## Architecture

The application follows a simple layered architecture:

```text
FHIR JSON Bundle
       |
       v
FHIR Pydantic Models
       |
       v
Loader
       |
       v
Normalizer / Reconciliation
       |
       v
Normalized Patient Summary
       |
       v
FastAPI
       |
       v
Next.js / React Frontend
       |
       v
Clinical Snapshot
```

### Backend

The backend is responsible for:

1. Loading the FHIR Bundle.
2. Validating/parsing the required FHIR resources.
3. Selecting the canonical patient.
4. Filtering invalid or non-current resources.
5. Preserving missing or uncertain information.
6. Handling unresolved references.
7. Preserving source date precision.
8. Producing a frontend-friendly patient summary.
9. Exposing the summary through a FastAPI endpoint.

### Frontend

The frontend consumes the normalized patient-summary API and displays:

- Patient demographics
- Active problems
- Active medications
- Allergies
- Relevant/recent encounters
- Relevant observations
- Data-quality and uncertainty information

The UI is intentionally designed to be simple and scannable rather than highly polished or feature-heavy.

---

## Technology Stack

### Backend

Versions below are the ones the project is currently developed and verified against.

- Python 3.14
- FastAPI 0.141.1
- Pydantic 2.13.5
- Uvicorn 0.52.4
- pytest 9.1.1

### Frontend

- TypeScript
- React
- Next.js

No database is required for this assessment.

Exact pinned versions are recorded in `requirements.txt`.

---

## Project Structure

The current structure is:

```text
Clinical Snapshot/
├── backend/
│   ├── app/
│   │   ├── main.py               FastAPI application
│   │   ├── api/                  HTTP routes
│   │   ├── models/               Pydantic models (FHIR + summary)
│   │   └── services/
│   │       └── loader.py         Reads the raw FHIR Bundle
│   └── tests/                    Safety-focused backend tests
│
├── frontend/                     Next.js clinical snapshot (to be built)
│
├── docs/
│   ├── README.md                 This document
│   ├── CLAUDE_PROJECT_GUIDE.md   Implementation guide
│   └── scenario1_clinical_snapshot_CANDIDATE_1[76].pdf
│
├── raw_data/
│   └── scenario1_fhir_bundle[78].json    Provided input, never modified
│
├── normalized_data/              Cleaned/normalized output (see below)
│
├── requirements.txt
└── .gitignore
```

Files not yet created are listed in *Implementation Status*.

### `raw_data/` and `normalized_data/`

`raw_data/` holds the provided Bundle exactly as supplied. It is treated as
read-only input and is never edited in place, so the original messy data
always remains available for comparison.

`normalized_data/` is used to store the cleaned, normalized output as a backup
or for inspection when needed.

Importantly, `raw_data/` remains the single source of truth at runtime: the API
normalizes the Bundle in memory on each request rather than reading from
`normalized_data/`. This means a stored normalized file can never silently
become stale clinical data being served to the frontend.

---

# Normalization and Reconciliation Decisions

## Canonical Patient

The Bundle contains two Patient resources:

```text
patient-001
patient-002
```

They contain overlapping demographic information but also conflicting fields such as phone numbers and MRNs.

For this application, `patient-001` is selected as the canonical patient.

### Reason

`patient-001` is referenced by the primary clinical resources and contains richer demographic information.

The application does **not** silently merge conflicting fields from `patient-002` into `patient-001`.

This is an explicit implementation assumption rather than a claim that the two Patient resources have been conclusively proven to represent the same individual.

### Current rule

```text
Canonical patient = patient-001
```

Clinical resources are attributed to the canonical patient based on their explicit patient references.

---

## Resource Status Handling

Resources with statuses indicating that they are invalid, historical, stopped, inactive, resolved, or entered-in-error are not presented as current clinical facts.

Status handling is performed according to the semantics of each resource rather than using one generic rule for every FHIR resource.

### Current decisions

| Resource | Status | Decision |
|---|---|---|
| `encounter-001` | finished | Include |
| `encounter-002` | entered-in-error | Exclude |
| `condition-001` | active + confirmed | Include |
| `condition-002` | inactive + entered-in-error | Exclude |
| `condition-003` | active + confirmed | Include with uncertainty |
| `observation-001` | final | Include |
| `observation-002` | final | Include with uncertainty |
| `observation-003` | final | Include |
| `observation-004` | entered-in-error | Exclude |
| `medicationrequest-001` | active | Include |
| `medicationrequest-002` | stopped | Exclude from active medications |
| `medicationrequest-003` | active, patient-002 | Exclude from patient-001 snapshot |
| `allergyintolerance-001` | active + confirmed | Include |
| `allergyintolerance-002` | resolved + entered-in-error | Exclude from current allergies |
| `allergyintolerance-003` | active + unconfirmed | Include with uncertainty |

---

## Missing Coding Displays

The source may contain a coding system and code without a human-readable `display`.

The application does not invent a display value.

For example:

```text
system: http://loinc.org
code: 4548-4
display: unavailable
```

The normalized representation preserves the code and indicates that the display is unavailable.

The frontend communicates this explicitly rather than presenting a guessed clinical name.

Example:

```text
Code: 4548-4
Display name unavailable
```

---

## Unresolved References

Some resources reference resources that are not present in the Bundle.

For example:

```text
Encounter/encounter-099
```

is referenced by `condition-003`, but that Encounter is not present in the supplied Bundle.

The application:

- Does not crash.
- Does not invent the missing resource.
- Does not silently remove the reference.
- Preserves the original reference where useful.
- Marks the reference as unresolved.

Example normalized representation:

```json
{
  "encounter": null,
  "encounter_reference": "Encounter/encounter-099",
  "reference_resolved": false
}
```

Unresolved-reference information may also be surfaced through the data-quality section.

---

## Date Precision

The source contains dates with different levels of precision.

Examples include:

```text
1958-03-12
2025-11-04T14:15:00Z
2020
2019
2022
2015
```

The application preserves the precision provided by the source.

For example:

```text
2020
```

will not be converted into:

```text
2020-01-01
```

because doing so would introduce information that was not present in the source.

---

## Uncertainty Handling

The application intentionally communicates uncertainty rather than hiding it.

Examples include:

```text
Unconfirmed
Display name unavailable
Reference could not be resolved
Unknown
```

An uncertain record should not be visually presented in the same way as a confirmed/current record when that would create a misleading impression of certainty.

For example, the active but unconfirmed allergy is retained and shown as unconfirmed rather than being discarded or presented as a confirmed allergy.

---

# Normalized Patient Summary

The API is designed to return a simplified representation intended for frontend consumption rather than exposing the raw FHIR Bundle.

The planned response shape is:

```json
{
  "patient": {
    "id": "patient-001",
    "name": "...",
    "birth_date": "...",
    "gender": "...",
    "phone": "...",
    "address": "..."
  },
  "problems": [],
  "medications": [],
  "allergies": [],
  "encounters": [],
  "observations": [],
  "data_quality": []
}
```

The exact Pydantic response models will be finalized during implementation.

---

# API

The planned patient-summary endpoint is:

```http
GET /api/patients/{patient_id}/summary
```

Example:

```http
GET /api/patients/patient-001/summary
```

The endpoint will:

1. Validate the requested patient ID.
2. Load the FHIR Bundle.
3. Normalize the relevant data.
4. Return the normalized patient summary.
5. Handle invalid or unresolved references safely.
6. Return an appropriate error when the requested patient cannot be found.

FastAPI's interactive documentation will also be available through:

```text
/docs
```

---

# Frontend

The frontend will provide a single-page clinical snapshot.

The planned layout is approximately:

```text
Patient Demographics

Active Problems        Medications

Allergies              Recent Encounters

Relevant Observations

Data Quality / Uncertainty
```

The interface prioritizes:

- Fast scanning
- Clear hierarchy
- Readability
- Explicit uncertainty
- Avoiding fabricated information

The frontend will not attempt to hide data-quality problems simply to make the interface look cleaner.

---

# Testing

Testing will focus primarily on the data-safety and normalization decisions.

Planned tests include:

- Entered-in-error Encounter is not shown as a current/recent encounter.
- Inactive/entered-in-error Condition is not shown as an active problem.
- Active confirmed Condition is retained.
- Stopped MedicationRequest is not shown as an active medication.
- Confirmed Penicillin allergy is retained.
- Unconfirmed allergy is retained with visible uncertainty.
- Entered-in-error/resolved allergy is not shown as a current confirmed allergy.
- Missing coding display does not result in an invented display.
- Unresolved references do not crash normalization.
- Unresolved references remain represented where appropriate.
- Partial dates retain their original precision.
- Canonical patient selection follows the documented rule.
- Resources belonging to the non-canonical patient are not incorrectly attributed to the canonical patient.

The test suite will prioritize meaningful normalization and safety decisions rather than large numbers of trivial tests.

---

# Clinical Safety Principles

The implementation follows these principles:

1. Never invent clinical facts.
2. Never silently merge conflicting patient data.
3. Never treat an unavailable reference as resolved.
4. Never turn a partial date into a more precise date.
5. Never invent a coding display when the source does not provide one.
6. Do not present entered-in-error data as current clinical fact.
7. Do not present inactive, stopped, or resolved resources as current without an appropriate reason.
8. Preserve uncertainty where it affects interpretation.
9. Keep assumptions explicit and documented.
10. Prefer deterministic and conservative behavior.

---

# Running the Application

Requires Python 3.13 or newer. The commands below are run from the project root
unless stated otherwise.

## Environment setup

Create and activate a virtual environment, then install the dependencies.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Backend

The application module is `app.main`, resolved relative to the `backend`
directory. The server must therefore be started from `backend`:

```bash
cd backend
uvicorn app.main:app --reload
```

The API is then available at:

```text
http://127.0.0.1:8000/          Service check
http://127.0.0.1:8000/docs      FastAPI interactive documentation
```

Once implemented, the patient summary endpoint will be available at:

```text
http://127.0.0.1:8000/api/patients/patient-001/summary
```

## Tests

Tests are also run from the `backend` directory, so that `app` resolves
correctly on the import path:

```bash
cd backend
pytest
```

No tests exist yet; see *Implementation Status*.

## Frontend

Not yet scaffolded. Instructions will be added once the Next.js application
exists.

---

# Development Decisions

The implementation intentionally avoids unnecessary complexity.

The following are not required for the core assessment:

- Database
- Authentication
- Deployment
- Advanced search
- Complex state management
- Animations
- Advanced UI features
- Full FHIR R4 implementation

The priority is correctness, safe data handling, a working API, a working frontend, meaningful tests, and clear documentation.

---

# Open Decisions

The following questions materially affect the normalizer and are recorded here
rather than being resolved silently in code. Each will be settled, implemented,
and documented with its rationale before the normalizer is considered complete.

**1. The active medication on the non-canonical patient.**
`medicationrequest-003` is `active` but belongs to `patient-002`. Excluding it
from the canonical patient's medication list is correct, because attributing it
would mean silently merging two records that the Bundle never links. However,
excluding it without trace would hide an active prescription. The current
intention is to exclude it from Active Medications while reporting it in the
data-quality section as an active medication on an unmerged duplicate record.

**2. Suspected false precision.**
Values such as `2018-01-01T00:00:00Z` are valid full timestamps, but midnight
on the first of January is a common artifact of a year-only value being padded
upstream. The choice is between presenting the data literally and flagging it
as suspected coarser precision.

**3. The reference point for "recent" encounters.**
`Bundle.timestamp` is later than every event in the Bundle, and the real
current date is later still. Anchoring recency to the current date would cause
the meaning of "recent" to drift over time. Options are to anchor to
`Bundle.timestamp`, to omit a recency window entirely, or to label encounters
with their age relative to a stated reference point.

**4. The malformed allergy coding.**
`allergyintolerance-001` pairs the SNOMED CT system with a code that is not
SNOMED-shaped, while supplying the display "Penicillin". The choice is between
trusting the supplied display and additionally marking the coding as suspect.

**5. Possible duplicate allergy.**
`allergyintolerance-003` carries a SNOMED-shaped code with no display, and may
denote a concept overlapping `allergyintolerance-001`. Its meaning is not
inferred, since doing so would amount to guessing a display value. Both failure
modes carry risk: an unnoticed duplicate clutters the allergy list, while a
wrongly assumed duplicate could suppress a distinct allergy. Verification would
require a terminology service, which is out of scope here, so both entries are
retained and the uncertainty is surfaced.

---

# Tradeoffs

This section will be updated as implementation decisions are made.

Current tradeoffs include:

- A limited subset of FHIR R4 is modeled instead of implementing the complete specification.
- `patient-001` is selected as the canonical patient based on the available Bundle evidence and documented as an assumption.
- Conflicting demographic fields are not silently merged.
- Missing terminology display values are not guessed.
- Unresolved references are preserved rather than fabricated or silently discarded.
- Source date precision is preserved instead of normalized into artificial precision.

---

# What Would Be Improved With More Time

This section will be updated after the core implementation is complete.

Potential areas for future improvement may include:

- More comprehensive FHIR resource support.
- More extensive normalization rules.
- Additional test coverage for unusual FHIR structures.
- More sophisticated reference resolution across external sources.
- More comprehensive terminology handling.
- Additional frontend accessibility and usability improvements.
- Production deployment considerations.

These improvements are intentionally deferred until the core requirements are complete and tested.

---

# AI-Assisted Development

AI tools are being used as development assistants rather than autonomous decision-makers.

Important implementation decisions are reviewed against:

1. The assessment requirements.
2. The actual FHIR input data.
3. Clinical/data-safety considerations.
4. Tests demonstrating the intended behavior.

Specific AI usage, tools/models, examples of acceleration, and examples where AI suggestions were corrected or rejected will be documented separately in:

```text
AI_USAGE.md
```

---

# Definition of Done

## Backend

- [x] Bundle loads successfully.
- [x] FastAPI application runs and `/docs` is available.
- [ ] Required FHIR resources are modeled with Pydantic.
- [ ] Patient reconciliation is implemented and documented.
- [ ] Invalid/error statuses are handled.
- [ ] Active/inactive/stopped/resolved states are handled appropriately.
- [ ] Missing coding displays are handled safely.
- [ ] Broken references are handled safely.
- [ ] Date precision is preserved.
- [ ] Patient summary response works.
- [ ] Patient summary endpoint is exposed.
- [ ] CORS is configured for the frontend origin.
- [ ] Backend tests pass.

## Frontend

- [ ] Patient demographics are displayed.
- [ ] Active problems are displayed.
- [ ] Active medications are displayed.
- [ ] Allergies are displayed.
- [ ] Recent/relevant encounters are displayed.
- [ ] Relevant observations are displayed.
- [ ] Uncertainty is visible.
- [ ] Missing information is not fabricated.
- [ ] No major console/build errors.

## Submission

- [x] README.md
- [x] Provided FHIR data
- [ ] AI_USAGE.md
- [ ] Backend
- [ ] Frontend
- [ ] Tests
- [ ] No secrets or API keys committed
- [ ] Application can be run using the documented instructions