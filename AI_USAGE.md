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
  components, and the shared uncertainty-handling primitives (`CodeLabel`
  for the "display unavailable" pattern) in one pass, then verified with
  `next lint`, `next build`, and a live run against the backend covering
  both the golden path and the error paths (patient not found, backend
  unreachable).
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
- **Bundle upload (scope addition).** Reused `build_patient_summary`/
  `list_patients` unchanged for uploaded data — they already took a plain
  dict, so the only new backend code was loading/merging files and an
  upload endpoint. Building this forced a real hardening pass: resource
  parsing (`_parse_resources`) now skips and logs a malformed resource
  instead of crashing the whole request, since uploaded data is no longer
  guaranteed well-formed the way the fixed demo file was.

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

**Self-caught: "non-canonical" silently meant "duplicate of patient-001," which
broke the moment a third patient existed.** `list_patients()` and the
cross-patient-medication flag both derived "is this a duplicate record?" from
`patient.id != CANONICAL_PATIENT_ID` — correct with exactly two patients (one
confirmed duplicate pair), but never actually meant that generally. Building
the upload feature made this observable for the first time: the first
end-to-end test uploaded an unrelated synthetic patient, and the API labeled
him "Not selected as the canonical record (see patient-001)" — asserting a
duplicate relationship to Dorothy Whitfield that was simply false. This
wasn't caught by reasoning about the code; it was caught by actually running
the new feature against real data and reading the response, which is why that
verification step matters. Fixed by replacing the implicit rule with an
explicit `KNOWN_DUPLICATE_PATIENT_IDS = {"patient-002"}` set — one
documented, human-reviewed id, not "everyone else" — and added a regression
test (`test_unrelated_uploaded_patient_is_not_flagged_as_duplicate`).

**Self-caught: encounters leaked across patients — the most significant bug
found in this project.** At the developer's request, generated a synthetic
12-patient test Bundle to exercise the upload feature at a realistic scale,
then actually uploaded it to a live (isolated — never the real `raw_data/`)
server and read every response rather than assuming the feature worked.
`patient-106`'s summary came back with four Encounters, none of which were
his: three belonged to other synthetic patients, and one —
`encounter-001` — belonged to `patient-001` in the *original* demo Bundle.
The cause: `build_patient_summary`'s `visible_encounters` list was built
from every `Encounter` in the entire (now merged, multi-file) dataset,
filtered only by status, never by which patient it belonged to. This bug
predates the upload feature entirely — it was already live in the
single-canonical-patient version of the app, just structurally invisible,
because there was only ever one patient (`patient-002`) whose encounter list
could have leaked into, and that list was already empty for unrelated
reasons. It took a dataset with more than one patient actually having
encounters to surface it. The same missing scoping also meant a Condition
could "resolve" its `encounter` reference to a different patient's
Encounter. Fixed by scoping the encounters dict to the requesting patient
*before* it's used for either the visible list or reference resolution, with
a regression test that specifically checks a condition referencing another
patient's real encounter does *not* resolve
(`test_encounters_are_scoped_to_the_requested_patient`). This is the
strongest evidence in this project for verifying live against real data
runs, rather than trusting that logic which looks correct actually is.

**Self-caught: non-canonical status was invisible on a duplicate record's own
page.** The developer asked what should happen when uploaded data includes a
duplicate/"NCR" patient, which prompted actually reading `PatientHeader.tsx`
rather than answering from memory of what was built earlier. Found that the
"NCR" badge only ever rendered on the patient-list card
(`components/PatientCard.tsx`); the individual snapshot page
(`/patients/{id}`) showed nothing — no badge, no explanation — for a
non-canonical patient. Someone navigating straight to `patient-002`'s own
page (a shared link, a direct URL) would see no indication it's a duplicate
record, directly contradicting this project's own principle that uncertain
data must not look the same as confirmed data. Fixed by adding
`is_canonical`/`note` to `PatientSummary` (previously only `PatientListItem`
carried them) and rendering the same badge + explanation on the header. Also
generalized `KNOWN_DUPLICATE_PATIENT_IDS` from a single hardcoded id to a
dict of documented pairs while fixing this, since demonstrating the fix
properly required a second real pair to test against — proven with
`test_a_second_known_duplicate_pair_works_independently_of_the_first`, which
also checks the two pairs' cross-patient-medication flags don't leak into
each other's canonical summaries (the same bug class as the encounter leak
above, caught proactively this time instead of via a live-server surprise).

**Note on developer review in this session.** The five open normalization
questions (see *Resolved Decisions* in `docs/README.md`) were presented to the
developer as explicit proposed rules with rationale before any code was
written, and approved as a batch. Later feature work (the upload persistence
model) involved a genuine architecture question put to the developer with
three options and their tradeoffs; the developer chose a fourth approach
(save uploads to `raw_data/`, merge all files on load) not among those
options. As a result, this session's clearest examples of course-correction
are self-caught (the two above) rather than the developer overriding a
specific AI-authored line of code after the fact — this section should be
updated with that kind of example if one arises, rather than fabricating one
here.

---

## Working Method

Each phase (open decisions &rarr; FHIR models &rarr; summary models &rarr;
normalizer + tests &rarr; API &rarr; frontend) was implemented, verified
against the real Bundle or a live server, and summarized to the developer
before moving to the next phase — a propose-review-accept loop rather than
generating the whole application in one pass.
