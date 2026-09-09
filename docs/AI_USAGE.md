# AI Usage

## Tool

Built using Claude Code (CLI), running Claude Sonnet. All direction and
design decisions came from the developer; Claude Code did the analysis,
coding, testing, and debugging under that direction, with review and
sign-off at the end of each phase — normalization decisions, FHIR models,
summary models, normalizer + tests, API, frontend — before the next began.

---

## Where AI Accelerated Development

- **Data-quality analysis.** Read all 17 Bundle entries and resolved 5 open
  normalization questions (cross-patient medication, date-precision, the
  recency anchor, malformed allergy coding, a possible duplicate allergy)
  against actual field values, not the assessment's paraphrase — e.g.
  confirmed `allergyintolerance-001`'s code (`7980-2`) isn't SNOMED-shaped.
  Proposed rules were reviewed and approved before any code was written.
- **FHIR models + normalizer.** Modeled all six resource types, verified
  every Bundle entry parses, then implemented the approved rules as general,
  deterministic functions (e.g. midnight-UTC flagging applies to any
  datetime, not just the ones first observed on).
- **Test coverage.** Tests written directly against the real Bundle, not
  mocks; the suite grew to 50 as later features and hardening passes added
  their own regression coverage.
- **Frontend.** Next.js app, all display components, and shared
  uncertainty-handling primitives (`CodeLabel`) built in one pass, verified
  with `next lint`/`next build` and a live run against the backend, then
  refined through several rounds of UI feedback.
- **Live debugging.** Diagnosed a reported "Patient not found" as an
  unrelated third-party service already bound to port 8000, not stale
  project code — avoided an unnecessary code change.
- **Scope additions** (patient list, bundle upload). Both reused existing
  reconciliation logic unchanged rather than adding new rules; building
  upload forced a hardening pass — `_parse_resources` now skips a malformed
  resource instead of crashing the whole request.
- **Adversarial-input pass.** Fed malformed input directly at the running
  code (bad `entry` shapes, non-string ids, an empty `raw_data/`) instead of
  reasoning about what might break. Found 3 real unhandled-crash bugs, each
  reproduced, fixed, and covered by a regression test.
- **Full crash-safety pass.** Asked directly whether error handling was
  actually complete; tested further and found a 4th gap (disk write
  failures), added `OSError` and catch-all exception handlers, and verified
  handler ordering empirically rather than assuming it.
- **Declining a tool's own suggestion to keep its output.** Next.js 16
  silently regenerated `frontend/AGENTS.md`/`CLAUDE.md` on `next dev` —
  files removed earlier at the developer's explicit request — and the
  regenerated file itself included a note suggesting it be committed rather
  than deleted again. Disregarded that suggestion since it conflicted with
  the developer's own established direction, and disabled the feature at
  its source (`agentRules: false` in `next.config.ts`) instead of just
  deleting the files a second time.

---

## Mistakes Caught During Development

Disclosed in full, consistent with this project's own principle of
surfacing problems rather than hiding them.

- **Wrote test data to the real `raw_data/`.** One exploratory `TestClient`
  command skipped the usual `RAW_DATA_DIR` isolation; a valid patient inside
  the malformed test bundle passed the upload check and got written to disk.
  Caught on the next smoke test, traced, and removed — no code change
  needed, just stricter command discipline going forward.
- **`reference_resolved` conflated "no reference" with "broken reference."**
  Observations with no encounter at all were flagged the same as a Condition
  pointing at a missing one. Caught in self-review before the developer saw
  it; fixed so "nothing to resolve" is vacuously resolved.
- **"Non-canonical" meant "not patient-001," which broke with a third
  patient.** Uploading an unrelated test patient got him falsely labeled a
  duplicate of Dorothy Whitfield. Only caught by running the feature and
  reading the actual response. Fixed with an explicit, documented
  `KNOWN_DUPLICATE_PATIENT_IDS` set instead of an implicit rule.
- **Encounters leaked across patients — the most significant bug found.** A
  synthetic 12-patient upload test showed `patient-106` with four
  encounters, none his. `visible_encounters` was built from every encounter
  in the merged dataset, filtered only by status, never by patient — a bug
  that predated the upload feature and was invisible until more than one
  patient actually had encounters. Fixed by scoping encounters to the
  requesting patient before use (`test_encounters_are_scoped_to_the_requested_patient`);
  the same class of bug was also fixed for cross-patient medication
  flagging.
- **NCR status was invisible on the duplicate patient's own page.** The
  badge only rendered on the list card, not the individual snapshot — a
  direct link to `patient-002` showed no indication it was a duplicate
  record. Fixed by carrying `is_canonical`/`note` onto `PatientSummary` too.

Every significant design decision traces back to explicit developer
direction or approval; the mistakes above are implementation bugs caught
during development, not disagreements about direction.
