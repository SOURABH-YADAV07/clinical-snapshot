# Clinical Snapshot

A full-stack application that ingests a synthetic FHIR R4 Bundle, reconciles the clinical data conservatively, and presents a safe, scannable patient clinical snapshot — built as a take-home assessment for Centauri Health Solutions.

The priority throughout is **clinical/data safety and honest communication of uncertainty** over completeness or polish: the app never invents a clinical fact, never silently merges conflicting patient records, and never presents incomplete or unverified data as though it were confirmed.

---

## Overview

- Loads and reconciles a FHIR R4 Bundle (`Patient`, `Encounter`, `Condition`, `Observation`, `MedicationRequest`, `AllergyIntolerance`).
- Excludes resources that shouldn't be presented as current clinical fact (entered-in-error, inactive, stopped, resolved).
- Preserves uncertainty instead of hiding or guessing it — missing coding displays, unresolved references, imprecise dates, and unconfirmed records are shown, never fabricated.
- Exposes a normalized patient-summary API (FastAPI) and a one-page clinical snapshot (Next.js/TypeScript).
- Supports uploading additional FHIR Bundles from the frontend, beyond the assessment's original single-bundle scope.

The provided data (`raw_data/scenario1_fhir_bundle[78].json`, 17 entries) intentionally contains production-like problems: two conflicting `Patient` records for the same apparent person, entered-in-error/inactive resources, missing coding displays, references to resources absent from the Bundle, dates at varying precision, and a US Core race/ethnicity extension. See *Normalization & Reconciliation Decisions*.

---

## Architecture

```text
FHIR JSON Bundle(s) in raw_data/
       |
       v
FHIR Pydantic Models   backend/app/models/fhir.py
       |
       v
Loader                 backend/app/services/loader.py — loads & merges every raw_data/*.json
       |
       v
Normalizer             backend/app/services/normalizer.py — reconciliation & safety rules
       |
       v
Normalized Summary     backend/app/models/summary.py
       |
       v
FastAPI                backend/app/api/
       |
       v
Next.js / React         frontend/
```

No database — the API normalizes the merged Bundle in memory on every request, so there's never a stored, potentially-stale normalized copy being served.

```text
backend/app/
├── main.py            FastAPI app
├── api/                patients.py, bundles.py
├── models/             fhir.py, summary.py
└── services/           loader.py, normalizer.py

frontend/src/
├── app/                page.tsx (home), patients/, patients/[patientId]/, upload/
├── components/         one per snapshot section, plus Navbar, CodeLabel
├── lib/                API client, date/title-case formatting, partition
└── types/               mirrors the summary API response
```

---

## Tech Stack

**Backend:** Python, FastAPI, Pydantic, pytest — exact pinned versions in `requirements.txt`.
**Frontend:** TypeScript, React, Next.js (App Router).

---

## Local Setup

**Prerequisites:** Python 3.13+, Node.js 18+, Git. Commands below run from the project root unless noted.

**1. Backend**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```
Verify: `http://127.0.0.1:8000/docs` loads the FastAPI interactive docs.

**2. Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```
Verify: `http://localhost:3000` loads the welcome page, and `/patients` shows the demo patients.

**3. Tests**
```bash
cd backend
pytest
```
50 tests (normalizer, loader, API), all passing.

**Configuration.** The frontend expects the backend at `http://127.0.0.1:8000` by default. To point it elsewhere, copy `frontend/.env.local.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_BASE_URL`.

**Troubleshooting.**
- *`uvicorn` fails to bind / port 8000 already in use:* something else on the machine is already using it — this happened during development (an unrelated local service, not this project). Find and stop whatever is bound to 8000 rather than moving this project to a different port, since `NEXT_PUBLIC_API_BASE_URL`'s default and the CORS origins in `backend/app/main.py` both assume the standard 8000/3000 pair. On Windows: `netstat -ano | findstr :8000` to find the PID, then `taskkill /PID <pid> /F`.
- *Frontend loads but shows "Could not load..." or "Patient not found":* the backend isn't reachable at the URL the frontend expects. Confirm `uvicorn` is actually running at `http://127.0.0.1:8000`. If the error message names a different port, that's almost always a stale `NEXT_PUBLIC_API_BASE_URL` left over in the terminal's environment from earlier — fully stop the frontend process and restart `npm run dev` in a clean shell.
- *CORS errors in the browser console:* the frontend's origin must be listed in `allow_origins` in `backend/app/main.py` (defaults cover `localhost:3000` and `127.0.0.1:3000`).
- *`frontend/AGENTS.md` or `CLAUDE.md` reappear:* Next.js 16 regenerates these on every `next dev`/`next build` by default. Disabled via `agentRules: false` in `frontend/next.config.ts` to keep the frontend free of AI-tooling artifacts; if they reappear, that setting is missing.

---

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/patients` | Lightweight list of every patient in the merged dataset, for the frontend's patient picker. |
| `GET /api/patients/{patient_id}/summary` | The normalized clinical snapshot for one patient. `404` if not found. |
| `POST /api/bundles` | Upload a new FHIR Bundle (JSON body). Validated, saved to `raw_data/`, returns the patients found in it. |

---

## Data

`raw_data/` holds every Bundle the API knows about. The original assessment file is never edited in place. Uploads (via `/upload` or `POST /api/bundles`) add new files here — never overwriting anything — and the loader merges every `.json` file on each request, so a new upload is live immediately with no restart. If two files define the same resource id, the first one loaded wins and the collision is logged, never silently overwritten.

Both the loader and the normalizer treat every Bundle file as untrusted input, not just the ones coming through `POST /api/bundles`: a file or resource that's missing, malformed, wrong-typed, or not JSON at all is skipped and logged rather than crashing the request. Beyond that, `backend/app/main.py` registers exception handlers so no endpoint ever returns Starlette's bare, unstructured "Internal Server Error": an empty `raw_data/` returns a clean `503` explaining why, a storage failure (permission denied, full disk) returns a `503` without leaking OS internals, and any other genuinely unexpected exception still gets logged in full server-side but returns a generic `500` to the client rather than a stack trace.

`normalized_data/` is a backup/inspection copy only — the API never reads from it, so it can never serve stale data.

Sample multi-patient Bundles for exercising the upload feature are in `test-data/` (gitignored).

---

## Normalization & Reconciliation Decisions

**Canonical patient.** The Bundle contains two conflicting `Patient` records (`patient-001`, `patient-002`) with no `Patient.link` or `meta.lastUpdated` to arbitrate between them. `patient-001` is treated as canonical (richer demographics, referenced by the clinical resources) — an explicit, documented assumption, not a claim of proven identity. Conflicting fields are never silently merged; `patient-002`'s own active medication is excluded from `patient-001`'s summary and reported in Data Quality instead. This relationship is tracked in `KNOWN_DUPLICATE_PATIENT_IDS` (`services/normalizer.py`), which supports any number of documented pairs, not just this one — still never automated identity-matching, only explicit, human-reviewed assertions. A non-canonical record is labeled "NCR" everywhere it appears: the patient list card, and directly on its own snapshot page (via `PatientSummary.is_canonical`/`.note`), so navigating straight to it never hides that status.

**Resource status.** Entered-in-error, inactive, resolved, and stopped resources are excluded from their respective "current" lists, with semantics judged per resource type rather than one blanket rule.

**Missing coding displays.** Never guessed. The code/system is preserved and the frontend shows "Display name unavailable."

**Unresolved references.** Never invented, never silently dropped. Preserved and marked `reference_resolved: false`.

**Date precision.** Preserved exactly as given — `2020` is never turned into `2020-01-01`. Datetimes landing on exact midnight UTC are additionally flagged as suspected coarser precision.

**US Core extensions.** `Patient.extension` carries US Core race/ethnicity extensions (a coded OMB category plus a plain-language `text` sub-extension). The `text` value is surfaced as-is on the demographics header when present, falling back to the coding's own display if `text` is absent; nothing is shown, and nothing inferred, when the extension itself is absent (e.g. `patient-002`). Any other extension is preserved by lenient parsing but unused — only race/ethnicity are modeled.

**Uncertainty.** Surfaced, not hidden. Items with a missing display, an unresolved reference, or (for allergies) a non-confirmed verification status are shown separately from fully-known data — in their own "Incomplete or Unverified Items" section — rather than mixed into the main list with only a small text difference to notice. Routing is driven entirely by field values, never by resource id, so it responds correctly as source data changes.

---

## Clinical Safety Principles

1. Never invent clinical facts.
2. Never silently merge conflicting patient data.
3. Never treat an unavailable reference as resolved.
4. Never turn a partial date into a more precise date.
5. Never invent a coding display when the source doesn't provide one.
6. Don't present entered-in-error data as current clinical fact.
7. Don't present inactive, stopped, or resolved resources as current without reason.
8. Preserve uncertainty where it affects interpretation.
9. Keep assumptions explicit and documented.
10. Prefer deterministic, conservative behavior over inference.

---

## Testing

Focused on data-safety and normalization behavior rather than exhaustive coverage: status-based exclusion for each resource type, missing-display handling, unresolved-reference handling, date-precision preservation, canonical-patient selection, and cross-patient attribution — plus loader (multi-file merge, malformed-file handling) and API (validation, 404s, CORS) tests. 50 tests total; run with `pytest` from `backend/`.

---

## Tradeoffs

- A limited subset of FHIR R4 is modeled, not the full specification.
- `patient-001` is selected as canonical based on available evidence, documented as an assumption rather than a proven fact.
- Missing terminology displays and duplicate-record identity are never guessed — both would require a real terminology/matching service, out of scope here.
- No database, auth, or deployment tooling — not required for this assessment.

---

## What Would Be Improved With More Time

- Fuller FHIR resource support and terminology handling.
- Automated patient-matching (with a real terminology/MPI service) instead of the current single documented duplicate pair.
- More extensive frontend accessibility and usability polish.
- Production-readiness: auth, rate limiting on uploads, structured logging/monitoring.

---

## AI-Assisted Development

Built with Claude Code as a development assistant, with important decisions reviewed against the assessment requirements, the actual data, and clinical-safety considerations rather than accepted automatically. See `AI_USAGE.md` for tool/model details, concrete examples of acceleration, and real examples of mistakes caught and corrected during development.
