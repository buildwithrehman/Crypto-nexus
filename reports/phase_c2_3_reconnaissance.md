# C2.3 Reconnaissance

## Current Architecture
The current backend accurately segregates case data into isolated `data/runs/<run_id>/case.duckdb` files, while the master `cryptonexus.db` operates as a global registry for `pipeline_runs`.
CPU-heavy analytical pipelines are cleanly dispatched from FastAPI to an independent local Python `subprocess.Popen()` worker (`backend.worker`). Communication from the worker back to the master database operates entirely via an internal REST endpoint (`PATCH /runs/{run_id}/internal/status`), ensuring SQLite thread safety and avoiding `ATTACH`/`MERGE` violations.

## Run Lifecycle
1. **Creation**: `POST /runs` creates an `INITIALIZED` record.
2. **Upload**: `POST /runs/{run_id}/ingest` handles `multipart/form-data` uploads (.csv, .json, .xml).
3. **Dispatch**: `POST /runs/{run_id}/execute` assigns a `worker_pid`, updates status to `QUEUED`, and spawns the subprocess. Returns HTTP 202.
4. **Execution**: Worker starts, calling the internal API to set status to `RUNNING`.
5. **Progress**: The worker iterates over 10 distinct logical stages, updating `current_stage` in real-time.
6. **Completion**: Worker signals `COMPLETED` or `FAILED` via the internal API.

## Frontend State
- **Run Discovery**: The `Landing.tsx` UI hardcodes `run_e2e_phase_b` (DEMO_V1) exclusively.
- **Client Capabilities**: `frontend/src/lib/api.ts` contains typings for `RunResponse` and functions for `getRuns()`/`getRun()`, but lacks methods for `createRun`, `uploadFile`, or `executeRun`.
- **UI Gaps**: 
  - Cannot discover or select NEW_RUNs.
  - Cannot upload datasets.
  - Does not poll the server for active job status.
  - Cannot navigate into a newly processed case context dynamically.

## Progress State
- **Available Fields**: `status`, `current_stage`, `failed_stage`, `error_message`, `start_timestamp`.
- **Stages Tracked**: `INGEST`, `GEOIP`, `CORRELATION`, `CIH`, `GRAPH`, `GRAPH_ANALYSIS`, `FEATURES`, `ML_SCORING`, `ALERTS`, `FINALIZE`.
- **Accuracy**: Stage progress is rigidly categorical. **There are no percentage calculations.** Progress must be treated as approximate block-level milestones by the UI.

## Upload/Execute Flow
- **Backend Flow**: Mature and verified.
- **Frontend Flow**: Non-existent. A complete modal or dedicated page is required to handle file selection, upload streaming, and the handoff to the execution polling view.

## Recovery
- **Sync Thread Monitor**: FastAPI spins off `monitor_worker_process_sync` to await the `Popen` exit. If the process dies without emitting a terminal status, the thread catches it and marks the run `FAILED`.
- **Startup Reaping**: `backend/api/main.py` explicitly iterates over `QUEUED`/`RUNNING` jobs on startup, performing `os.kill(worker_pid, 0)`. If the worker is dead, it is safely marked as `FAILED`.
- **Gap**: The frontend currently has no websocket or polling loop, meaning a user staring at an active run will not know it crashed unless they manually refresh the page (which they can't currently do since the UI doesn't expose the run).

## Architecture Constraints
- `DEMO_V1` must remain untouchable.
- `NEW_RUN` analytical queries must remain routed directly to `case.duckdb`.
- No `ATTACH`/`MERGE`.
- No cancellation features are authorized.
- No heavy infrastructure (Redis/Celery/Kafka).
- The worker remains a standard Python local subprocess.

## Gaps
1. **Frontend API Client**: Missing `POST` functions for run lifecycle.
2. **Frontend UI State**: No global context or router mechanism to pivot the active `runId` away from `run_e2e_phase_b`.
3. **Frontend Upload UI**: No drag-and-drop or file selector.
4. **Frontend Polling UI**: No visual stepper or queue tracker utilizing the 10 progress stages.

## Proposed C2.3 Scope
1. Update `api.ts` to support Run creation, Upload, and Execution.
2. Build a "Run Manager" or "Upload Dataset" UI component on the Landing page.
3. Implement a polling hook (e.g., `useRunStatus(runId)`) that fetches `GET /runs/{run_id}` every few seconds until terminal status is reached.
4. Build a visual progress stepper mapping the backend's `current_stage` strings to the existing 9 visual blocks described in `Landing.tsx`.
5. Update the Investigation Navigation to use dynamic `/:runId/alerts` routing based on the selected run.

## Required Tests
- **Frontend Unit/Integration**: Verifying `apiClient` correctly serializes FormData.
- **Lifecycle Integration Test**: A simulated browser/API flow utilizing `valid_test.csv` to prove the UI can seamlessly upload, poll, and navigate to the resulting 0-alert dashboard.

## Risks
- **Large File Uploads**: Single-request multipart uploads might block or timeout on extremely large datasets. (Out of scope to fix via chunking, but worth noting).
- **Navigation Race Conditions**: The user must be firmly blocked from entering `/:runId/alerts` until the status strictly returns `COMPLETED`.

## Recommendation
Approve the Proposed C2.3 Scope strictly limiting work to **Frontend React/TypeScript implementation**. The backend requires zero modification to achieve Phase C2.3.
