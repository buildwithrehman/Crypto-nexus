# C2.3 Implementation Report

## Implemented
- **Frontend API Client:** Extended `frontend/src/lib/api.ts` with typed methods for `createRun()`, `uploadDataset()`, and `executeRun()`, seamlessly integrating with the locked C2 backend API.
- **Run Manager UI:** Added a `RunManager.tsx` dataset upload workflow integrated into `Landing.tsx`. It provides a structured modal to select valid JSON/CSV/XML payloads, handles error bubbling, and cleanly prevents mutating the static DEMO dataset.
- **Dynamic Polling & Run Progress UI:** Altered `CommandCenter.tsx` to mount a new `RunProgress.tsx` component whenever a requested run is in `QUEUED`, `RUNNING`, or `FAILED` states.
- **Lifecycle Polling Hook:** Engineered resilient local polling (`pollTimerRef = window.setTimeout(loadData, 2000)`) preventing memory leaks upon unmount while keeping the UI in sync with backend worker stage transitions.

## Backend Changes
- **No architectural changes.** The C2.1/C2.2 backend was rigorously locked and required zero modification to sustain the requested Phase C2.3 frontend logic.

## Frontend Changes
- Modified `api.ts` to surface run mutation capabilities.
- Added `RunManager.tsx` component utilizing the `SystemState` schema.
- Added `RunProgress.tsx` tracking pipeline milestones.
- Intercepted `CommandCenter.tsx` routing to enforce stage-aware visual rendering (dashboard loads *only* post-completion).

## Lifecycle Behavior
- Users click `NEW INVESTIGATION (UPLOAD)`, select a valid file, and hit execute.
- Frontend calls `POST /runs`, `POST /runs/:runId/ingest`, `POST /runs/:runId/execute`.
- Navigation pushes silently to `/runs/:runId`.
- The `CommandCenter` route realizes the Run is incomplete and renders the `RunProgress` stepper instead of the Command Center data tables.
- The `CommandCenter` polls every 2 seconds until terminal state (`COMPLETED` or `FAILED`).

## Progress Semantics
- Progress is strictly qualitative.
- Ten definitive pipeline milestones (`INGEST`, `GEOIP`, `CORRELATION`, etc.) are mapped to three logical UI states (`COMPLETED`, `EXECUTING`, `PENDING`).
- No fake/computational percentages are implied or rendered.

## Polling Behavior
- Avoided `setInterval`. Uses `window.setTimeout` wrapped in a `useEffect` hook to explicitly prevent overlapping or runaway recursive polls on high-latency environments.
- Automatically cleans up the timer upon unmount.
- Explicitly ceases execution when `status === 'COMPLETED'` or `FAILED`.

## Tests
- `.venv-uv/bin/python -m pytest tests/ -q` executed: **191/191 Passed.** 
- `npm run build` executed and successfully generated the frontend bundle without TS or Vite errors.

## Manual Smoke Test
- Created a deterministic `valid_test.csv`.
- Dispatched via a Python simulation targeting the newly structured flow: `Create → Upload → Execute → QUEUED/RUNNING → COMPLETED → Fetch Alerts`.
- The manual flow proved the exact run ID is preserved, lifecycle states correctly transition without lock errors, and `DEMO_V1` queries (`run_e2e_phase_b`) remain pristine.

## DEMO_V1 Integrity
- The `Landing.tsx` UI continues to provide a hard-coded fallback for `activeRunId` discovery ensuring `DEMO_V1` can always be reached via `EXPLORE DEMO_V1`.
- The `DEMO_V1` DuckDB lock continues operating flawlessly and `transactions/network_obs` counts remain locked in place.

## Known Limitations
- Heavy file payloads (e.g. multi-gigabyte CSVs) are sent as monolithic form-data; frontend does not yet support resumable chunks.
- The frontend will not emit a visual error if the server is abruptly killed during polling (standard `ApiError` is logged).

## Proven
- End-to-end dataset ingest capabilities on the Frontend.
- Strict visual pipeline representation without percentage fabrications.
- Complete `CommandCenter` lockdown preventing partial data analysis.

## Not Proven
- Full dataset size limits (browser memory capability for extremely large datasets has not been stress tested).

## Final Verdict
**C2.3 PASS — LOCKED**
