# AI Usage

## Tool and Models

This project was built using Claude Code (CLI), running on Claude Sonnet 5
(`claude-sonnet-5`). Work proceeded incrementally through explicit phases —
normalization decisions, FHIR models, summary models, the normalizer and its
tests, the API endpoint, then the frontend — with the developer reviewing and
signing off at each phase before the next began, rather than the whole
application being generated in one pass.

---

## Where AI Accelerated Development

- **Data-quality analysis of the raw Bundle.** Read all 17 entries directly
  and cross-checked every one of the 5 open normalization questions (the
  cross-patient medication, suspected date-precision, the recency anchor, the
  malformed allergy coding, the possible duplicate allergy) against the actual
  field values before proposing a rule — e.g. confirming that
  `allergyintolerance-001`'s code (`7980-2`) genuinely isn't SNOMED-shaped, and
  that three specific fields land on exact midnight UTC, rather than reasoning
  from the assessment's paraphrase of the data.
- **FHIR Pydantic models.** Modeled `Patient`, `Encounter`, `Condition`,
  `Observation`, `MedicationRequest`, and `AllergyIntolerance`, then verified
  all 17 Bundle entries actually parse against them.
- **The normalizer.** Implemented the reconciliation rules as general,
  deterministic functions — e.g. "any datetime with an exact midnight-UTC time
  component is flagged" rather than special-casing the specific resource IDs
  it was first observed on — so the logic generalizes rather than overfitting
  to this one Bundle.
- **Test coverage.** Wrote 19 normalizer tests and 5 API tests directly
  against the real Bundle (not mocked fixtures), covering every documented
  safety case.
- **Frontend scaffolding.** Generated the Next.js app, all 7 display
  components, and the shared uncertainty-handling primitives (`CodeLabel`,
  `UncertaintyNotes`) in one pass, then verified with `next lint`, `next
  build`, and a live run against the backend covering both the golden path
  and the error paths (patient not found, backend unreachable).
- **Live debugging.** When the frontend showed "Patient not found" after
  being wired up, diagnosed it by curling the backend directly and
  discovering port 8000 was occupied by an unrelated third-party service (a
  "Nexora Technologies API"), not stale project code — avoided a
  misdiagnosis that could have led to unnecessary code changes.
- **Patient list feature (scope addition).** When asked to make patient-002
  reachable via a clickable card rather than only by URL, reused the existing
  reconciliation logic rather than adding new identity-guessing rules: the
  list endpoint labels a record "non-canonical" purely by comparing against
  the already-documented `CANONICAL_PATIENT_ID` constant, and confirmed live
  that `patient-002`'s own snapshot renders correctly (its own name, its own
  active medication, no fabricated display for its undisplayed RXNorm code).

---

## Where AI Was Corrected / Self-Corrected

**Self-caught: `reference_resolved` was ambiguous for "no reference at all."**
The first version of `_resolve_encounter_reference` in
`services/normalizer.py` returned `resolved=False` whenever a Condition or
Observation had no `encounter` reference at all (e.g. `observation-002`,
`observation-003`, which never reference an encounter) — the same value as a
genuinely broken reference (like `condition-003` &rarr; `Encounter/encounter-099`,
which is missing from the Bundle). A frontend checking `if
(!reference_resolved)` would have flagged both cases identically, implying a
data-quality problem where none exists for the first group.

This was caught during self-review immediately after the normalizer was
verified against the real Bundle, before the developer saw it. Fixed so
`reference_resolved` is vacuously `true` when there is nothing to resolve, and
`false` only when a reference exists but points at a resource absent from the
Bundle. Tests were re-run to confirm no other behavior changed.

**Note on developer review in this session.** The five open normalization
questions (see *Resolved Decisions* in `docs/README.md`) were presented to the
developer as explicit proposed rules with rationale before any code was
written, and approved as a batch. As a result, this session does not contain
a case of the developer rejecting or changing a specific AI proposal after
implementation — only the self-caught issue above. This section should be
updated with a real example if one arises from further review, rather than
fabricating one here.

---

## Working Method

Each phase (open decisions &rarr; FHIR models &rarr; summary models &rarr;
normalizer + tests &rarr; API &rarr; frontend) was implemented, verified
against the real Bundle or a live server, and summarized to the developer
before moving to the next phase — matching the propose-review-accept loop
described in `docs/CLAUDE_PROJECT_GUIDE.md`.
