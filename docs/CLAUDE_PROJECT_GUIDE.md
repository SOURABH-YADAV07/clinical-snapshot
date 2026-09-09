# Claude Implementation Guide — Clinical Snapshot Take-Home

## 1. Objective

Build the requested small full-stack application for the Centauri Health Solutions take-home assessment.

The application must:

1. Load the provided messy FHIR R4 Bundle JSON.
2. Model the resources needed by the application with Pydantic.
3. Normalize/reconcile the input into a clean, deduplicated, safe-to-display patient representation.
4. Expose a patient-summary API using Python/FastAPI.
5. Render a one-page clinical snapshot using TypeScript/React/Next.js.
6. Handle uncertainty explicitly instead of hiding missing/ambiguous information or guessing.
7. Include `README.md` and `AI_USAGE.md`.

The assessment explicitly prioritizes:
- Clinical/data safety
- Code quality
- Frontend clarity
- AI-tool judgment
- Communication/documentation

Do not optimize for unnecessary features or visual polish at the expense of correctness.

---

## 2. Important Working Principle

Act as an AI coding assistant, not as an autonomous decision-maker.

Before implementing important clinical-data decisions:
- Explain the proposed rule.
- Identify assumptions.
- Prefer deterministic, conservative behavior.
- Never invent clinical facts.
- Never silently merge conflicting data.
- Never treat an unavailable reference as resolved.
- Never turn a partial date into a more precise date.
- Never invent a human-readable coding display when the source does not provide one.

The developer must review and validate your suggestions before they are shipped.

---

## 3. Input Data

The provided file is:

`scenario1_fhir_bundle[78].json`

It is a synthetic FHIR R4 Bundle.

The Bundle contains 17 entries and includes resources such as:
- Patient
- Encounter
- Condition
- Observation
- MedicationRequest
- AllergyIntolerance

The data intentionally contains production-like data-quality problems.

Known issues from the assessment include:
- Multiple Patient resources with overlapping/conflicting fields
- Error/inactive resources
- Missing coding display values
- References to resources not present in the Bundle
- Inconsistent date precision
- US Core extensions

Treat the input as data of uncertain provenance.

---

## 4. Required Architecture

Use a simple structure. Do not over-engineer.

Suggested structure:

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
├── frontend/
│   ├── app/
│   └── components/
├── data/
│   └── scenario1_fhir_bundle[78].json
├── README.md
└── AI_USAGE.md
```

This is only a suggested structure. Keep the final structure simple and readable.

---

# 5. Backend Requirements

## 5.1 Technologies

Use:
- Python
- FastAPI
- Pydantic
- pytest for tests

Do not introduce a database unless genuinely necessary. It is not required for this assignment.

---

## 5.2 FHIR Models

Model only the FHIR fields/resources needed by the application.

At minimum, handle:

```text
Bundle
Patient
Encounter
Condition
Observation
MedicationRequest
AllergyIntolerance
```

Use optional fields where the source data may legitimately omit information.

Do not attempt to implement the complete FHIR R4 specification.

---

# 6. Normalization / Reconciliation

This is the most important part of the project.

Create a dedicated normalization layer, for example:

```text
services/normalizer.py
```

The normalizer should transform:

```text
Raw FHIR Bundle
      ↓
Normalized Patient Summary
```

The normalization logic should be deterministic, testable, and conservative.

---

## 6.1 Patient Reconciliation

The input contains two Patient resources:

```text
patient-001
patient-002
```

They have overlapping demographics but partially conflicting fields.

Known examples:

### patient-001
- Name: Dorothy M Whitfield
- DOB: 1958-03-12
- Phone: 555-014-2231
- MRN: MRN-48213
- Address: 482 Larkspur Lane, Springvale, OH 44011

### patient-002
- Name: Dorothy Whitfield
- DOB: 1958
- Phone: 555-014-9987
- MRN: MRN-48213-A
- Address: 482 Larkspur Ln, Springvale, OH 44011

Important:
- Do not silently merge conflicting fields.
- Do not assume that same name/address automatically proves identity.
- Inspect which patient the clinical resources actually reference.
- Prefer a deterministic canonical-patient rule.
- Document the rule and its limitations in `README.md`.

A reasonable implementation may choose `patient-001` as the canonical patient because the clinical resources reference it and it contains richer demographics, but this must be treated as an explicit documented assumption, not as an unquestionable clinical fact.

---

## 6.2 Resource Status Handling

Resources with statuses indicating invalid, historical, stopped, inactive, resolved, or entered-in-error must not be presented as current clinical facts.

Do not use one generic status rule for every FHIR resource without considering resource semantics.

Examples from the input:

### Encounter
`encounter-002`
- status: `entered-in-error`

It should not appear as a normal current/recent clinical encounter.

### Condition
`condition-001`
- clinicalStatus: `active`
- verificationStatus: `confirmed`
- code: I10 — Essential (primary) hypertension

This is appropriate for active problems.

### Condition
`condition-002`
- clinicalStatus: `inactive`
- verificationStatus: `entered-in-error`
- code: J45.909

Do not present it as an active/current problem.

### MedicationRequest
`medicationrequest-001`
- status: `active`
- Lisinopril 10 MG Oral Tablet
- Take one tablet by mouth once daily

This is an active medication.

### MedicationRequest
`medicationrequest-002`
- status: `stopped`
- Metformin 500 MG Oral Tablet

Do not present it as an active medication.

### Observation
`observation-004`
- status: `entered-in-error`

Do not present it as a current/relevant observation.

### AllergyIntolerance
`allergyintolerance-001`
- clinicalStatus: `active`
- verificationStatus: `confirmed`
- Penicillin
- criticality: `high`

This should be shown clearly.

### AllergyIntolerance
`allergyintolerance-002`
- clinicalStatus: `resolved`
- verificationStatus: `entered-in-error`
- Latex allergy

Do not present it as a current confirmed allergy.

### AllergyIntolerance
`allergyintolerance-003`
- clinicalStatus: `active`
- verificationStatus: `unconfirmed`
- code has no display
- criticality: `unable-to-assess`

Do not hide this. Show it with visible uncertainty.

---

# 7. Missing Coding Displays

FHIR codings may contain:

```json
{
  "system": "...",
  "code": "..."
}
```

without:

```json
"display": "..."
```

When `display` is missing:

- Do not guess the human-readable meaning.
- Preserve the coding system and code.
- Represent the display as unavailable.
- Let the frontend communicate that the display name is unavailable.

Example:

```json
{
  "system": "http://loinc.org",
  "code": "4548-4",
  "display": null,
  "display_available": false
}
```

The frontend may show:

```text
Code: 4548-4
Display name unavailable
```

---

# 8. Unresolved References

The Bundle contains a reference such as:

```text
Condition → Encounter/encounter-099
```

but the referenced Encounter does not exist in the Bundle.

Rules:

- Do not crash.
- Do not invent the missing resource.
- Do not silently remove the fact that the reference existed.
- Preserve the reference where useful.
- Mark it unresolved.

Example normalized representation:

```json
{
  "encounter": null,
  "encounter_reference": "Encounter/encounter-099",
  "reference_resolved": false
}
```

Consider including unresolved-reference information in a `data_quality` section.

---

# 9. Date Precision

The input contains dates with different precision.

Examples:

```text
1958-03-12
2025-11-04T14:15:00Z
2020
2019
```

Rules:

- Preserve the source precision.
- Do not convert `2020` into `2020-01-01`.
- Do not invent missing month/day/time values.
- Format dates for readability only when doing so does not create false precision.

---

# 10. Normalized API Response

Design a clean response model.

A reasonable shape:

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

Use Pydantic response models.

The response should be designed for frontend consumption rather than exposing the raw FHIR structure.

---

# 11. API

Implement:

```http
GET /api/patients/{patient_id}/summary
```

Example:

```http
GET /api/patients/patient-001/summary
```

The endpoint should:
1. Validate the patient ID.
2. Load the bundle.
3. Normalize the relevant data.
4. Return the normalized patient summary.
5. Handle invalid/missing references safely.
6. Return an appropriate error when the requested patient cannot be found.

Also ensure FastAPI's `/docs` endpoint works.

---

# 12. Backend Tests

Prioritize tests around data-safety decisions.

At minimum test:

1. `entered-in-error` Encounter is not shown as current/recent.
2. Inactive/entered-in-error Condition is not shown as an active problem.
3. Stopped MedicationRequest is not shown as an active medication.
4. Confirmed active Penicillin allergy is retained.
5. Unconfirmed allergy is retained with visible uncertainty.
6. Entered-in-error/invalid allergy is not shown as a current confirmed allergy.
7. Missing coding display does not result in an invented display.
8. Unresolved references do not crash normalization.
9. Partial dates retain their original precision.
10. Canonical patient selection follows the documented rule.

Do not spend time writing large numbers of trivial tests.

---

# 13. Frontend Requirements

## Technologies

Use:
- TypeScript
- React
- Next.js

Build a single-page clinical snapshot.

The goal is:

```text
Fast to scan
Clear
Readable
Honest about uncertainty
```

Not:

```text
Fancy
Animated
Over-engineered
```

---

# 14. Suggested UI

Structure the page approximately as:

```text
Patient Demographics
─────────────────────

Active Problems       Medications
─────────────────     ─────────────

Allergies             Recent Encounters
─────────────────     ────────────────

Relevant Observations
─────────────────────

Data Quality / Uncertainty
──────────────────────────
```

Suggested components:

```text
PatientHeader
Problems
Medications
Allergies
Encounters
Observations
DataQuality
```

---

# 15. Frontend Data Display Rules

## Demographics

Display:
- Name
- DOB
- Gender
- Phone if available
- Address if available

Do not fabricate missing values.

---

## Active Problems

Show current/appropriate problems only.

Example:

```text
Essential (primary) hypertension
Confirmed · Active
```

Do not show entered-in-error/inactive conditions as current facts.

---

## Medications

Show active medications.

Example:

```text
Lisinopril 10 MG Oral Tablet
Take one tablet by mouth once daily
```

Do not show stopped medication in the active medication section.

---

## Allergies

Clearly distinguish confidence/status.

Example:

```text
Penicillin
Confirmed · High criticality
```

For uncertain allergy:

```text
Unconfirmed allergy
Criticality: unable to assess
```

Do not make uncertain data look certain.

---

## Encounters

Show relevant valid/recent encounters.

Do not present `entered-in-error` encounters as normal clinical history.

---

## Observations

Show relevant observations such as:
- Blood pressure
- Weight
- Other valid relevant measurements

Do not display observations marked `entered-in-error` as current facts.

---

# 16. Data Quality / Uncertainty UI

Where appropriate, visibly communicate:

```text
Unconfirmed
Unknown
Display unavailable
Reference could not be resolved
```

Never hide uncertainty just to make the UI look cleaner.

---

# 17. AI Usage

The assessment requires `AI_USAGE.md`.

It must include:

## Tool and models
State which Claude tool/model was used.

## Where AI accelerated development
Give concrete examples.

## Where AI was corrected/rejected
Include at least one specific example where:
- Claude proposed something.
- You disagreed.
- You changed/rejected it.
- Explain why.

This section is important because the assessment explicitly evaluates whether the developer can direct and challenge the AI rather than blindly accept its output.

Do not fabricate examples. Record real examples from the actual development process.

---

# 18. README.md

Include:

```text
Project overview
Architecture
Tech stack
How to run backend
How to run frontend
API endpoint
Normalization/reconciliation decisions
Clinical safety decisions
Testing
Tradeoffs
What would be improved with more time
```

Especially document:
- Canonical patient decision
- Status filtering
- Missing coding display handling
- Unresolved references
- Date precision
- Uncertainty handling

---

# 19. Time Management

This must be completed today.

Prioritize in this order:

```text
1. Understand input
2. Pydantic models
3. Normalization/reconciliation
4. FastAPI API
5. Backend tests
6. Frontend snapshot
7. Uncertainty/data-quality UI
8. README
9. AI_USAGE.md
10. Final testing
```

If time becomes limited:

KEEP:
- Correct normalization
- Safe data handling
- Working API
- Working frontend
- Core tests
- README
- AI_USAGE.md

DROP/DEFER:
- Fancy UI
- Animations
- Database
- Authentication
- Deployment
- Advanced search
- Complex state management
- Unnecessary abstractions

---

# 20. Development Rules

Follow these rules throughout implementation:

1. Keep the code simple.
2. Prefer readable functions over clever abstractions.
3. Keep FHIR parsing separate from normalization.
4. Keep normalization separate from API routes.
5. Keep API models separate from raw FHIR models.
6. Never guess clinical facts.
7. Never silently discard uncertainty.
8. Never silently merge conflicting patient data.
9. Add tests for important normalization decisions.
10. Keep assumptions documented.
11. Do not add dependencies without a reason.
12. Do not expose the provided Claude API key in Git.
13. Do not commit secrets.
14. Run tests before declaring the project complete.

---

# 21. Working Method With Claude

Use Claude to:
- Explain unfamiliar FHIR concepts.
- Suggest implementation approaches.
- Generate initial code where useful.
- Review code.
- Suggest tests.
- Find edge cases.
- Review the normalization logic.

But for every important suggestion:

```text
Claude suggestion
       ↓
Developer review
       ↓
Validate against input/requirements
       ↓
Accept / modify / reject
```

Do not blindly accept generated code.

The final implementation must reflect deliberate engineering decisions.

---

# 22. Definition of Done

Backend:

- [ ] Bundle loads.
- [ ] Pydantic models work.
- [ ] Patient reconciliation works and is documented.
- [ ] Invalid/error statuses are handled.
- [ ] Active/inactive/stopped/resolved states are handled.
- [ ] Missing coding displays are handled safely.
- [ ] Broken references are handled safely.
- [ ] Date precision is preserved.
- [ ] Patient summary response works.
- [ ] FastAPI endpoint works.
- [ ] Tests pass.

Frontend:

- [ ] Patient demographics.
- [ ] Active problems.
- [ ] Active medications.
- [ ] Allergies.
- [ ] Recent encounters.
- [ ] Relevant observations.
- [ ] Uncertainty is visible.
- [ ] Missing information is not fabricated.
- [ ] No major console/build errors.

Submission:

- [ ] README.md
- [ ] AI_USAGE.md
- [ ] Backend
- [ ] Frontend
- [ ] Provided data
- [ ] Tests
- [ ] No secrets/API keys committed.

---

## Final Instruction to Claude

Help implement this project incrementally.

Do not generate the entire project blindly in one step.

Start by inspecting the provided FHIR JSON and proposing:
1. The exact data-quality issues.
2. The normalization/reconciliation rules.
3. The Pydantic models needed.
4. The normalized response schema.
5. The tests required for those decisions.

Wait for the developer to review important decisions before implementing large changes.

Always optimize for clinical data safety, correctness, simplicity, and demonstrable engineering judgment.
