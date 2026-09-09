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

- Python
- FastAPI
- Pydantic
- pytest

### Frontend

- TypeScript
- React
- Next.js

No database is required for this assessment.

---

## Project Structure

The intended structure is:

```text
project/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── fhir.py
│   │   │   └── summary.py
│   │   ├── services/
│   │   │   ├── loader.py
│   │   │   └── normalizer.py
│   │   └── api/
│   │       └── patients.py
│   └── tests/
│
├── frontend/
│   ├── app/
│   └── components/
│
├── data/
│   └── scenario1_fhir_bundle[78].json
│
├── README.md
└── AI_USAGE.md
```

This structure may be adjusted during implementation if a simpler organization proves more appropriate.

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

> This section will be completed once the backend and frontend setup are implemented.

## Backend

```text
TODO
```

## Frontend

```text
TODO
```

## Tests

```text
TODO
```

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

- [ ] Bundle loads successfully.
- [ ] Required FHIR resources are modeled with Pydantic.
- [ ] Patient reconciliation is implemented and documented.
- [ ] Invalid/error statuses are handled.
- [ ] Active/inactive/stopped/resolved states are handled appropriately.
- [ ] Missing coding displays are handled safely.
- [ ] Broken references are handled safely.
- [ ] Date precision is preserved.
- [ ] Patient summary response works.
- [ ] FastAPI endpoint works.
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

- [ ] README.md
- [ ] AI_USAGE.md
- [ ] Backend
- [ ] Frontend
- [ ] Provided FHIR data
- [ ] Tests
- [ ] No secrets or API keys committed
- [ ] Application can be run using the documented instructions