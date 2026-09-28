# Phase C2.5 Reconnaissance Report

## Context
Phase C2.4 successfully isolated workers into resilient local subprocesses, mapped the run registry durably into localized `case.duckdb` instances, and established offline/crash recovery protocols. The focus now turns to final jury/deployment readiness, emphasizing resource safety, UX for long-running workloads, and standalone packaging.

---

## A. CURRENT ARCHITECTURE
- **API/Worker Boundary:** FastAPI spawns `backend.worker` locally, directing stdout/stderr to an isolated `pipeline.log`.
- **Database Architecture:** `cryptonexus.db` holds the master registry; execution occurs strictly within `data/runs/<run_id>/case.duckdb`.
- **Recovery:** Startup hook introspects `case.duckdb` to gracefully revive orphaned runs.
- **Frontend Integration:** Uses `setInterval` polling in `RunProgress.tsx`, gracefully halting on `COMPLETED`/`FAILED`/`404`.

## B. FAILURE MODES
- **Loss of Session (Frontend):** If a user initiates a run, closes the browser, and returns later, they **lose access** to their investigation. `Landing.tsx` only hardcodes discovery of `DEMO_V1` and ignores the `GET /runs` API for user-generated cases.
- **Concurrency OOM:** Launching multiple runs sequentially forces parallel workers. Each worker strictly duplicates the ~1GB `hdbscan.joblib` and `isolation_forest.joblib` models into memory. On 16GB consumer laptops, >4 concurrent workers will trigger OS OOM kills.
- **Storage Leak (Orphaned Uploads):** While `MAX_FILE_SIZE` prevents malicious uploads, successful CSV files are **never deleted** from `data/runs/<run_id>/uploads/` after ingestion, leaking storage indefinitely.

## C. RESOURCE SAFETY
- **RAM Usage:** **UNVERIFIED / BLOCKER** - Concurrent workers linearly scale RAM consumption due to non-shared ML artifact loading.
- **Temporary Files:** **MISSING** - Source files aren't garbage collected post-ingestion.
- **Upload Size:** **PROVEN** - Checked at 100MB chunked via FastAPI limits.
- **DuckDB Lifecycle:** **PROVEN** - Strictly process-bound and auto-closes on worker termination.

## D. OBSERVABILITY
- **API Lifecycle:** **PROVEN** - API accurately surfaces `status`, `current_stage`, and `error_message`.
- **Frontend Stats:** **MISSING** - `CommandCenter.tsx` hardcodes dataset statistics as `"[DYNAMIC]"` (lines 192-212) rather than displaying the actual `transactions` and `network_obs` ingested into `case.duckdb`.
- **Log Exposure:** **PARTIAL** - `pipeline.log` is written natively by the OS pipe but cannot be downloaded/viewed via the UI.

## E. PERFORMANCE
- **In-process DuckDB:** **PROVEN** - Highly performant for isolated execution.
- **Bottlenecks:** Model loading dominates initial worker startup cost.

## F. DEPLOYMENT / OFFLINE
- **Python / Offline:** **PROVEN** - Environment strictly pinned in `requirements.txt`.
- **Single-Binary / Runtime (BLOCKER):** **MISSING** - FastAPI does *not* serve the frontend build (`dist`). Currently, a user must manually spin up Vite/Node (`npm run preview`) alongside Uvicorn. This violates the offline Python-only desktop/local runtime requirement.

## G. SECURITY / DATA SAFETY
- **PROVEN** - Stringent `run_id` path-traversal blocks, isolated directory environments, chunked ingestion streams, and protected `DEMO_V1` schema execution.

## H. CONCURRENCY
- **PROVEN** - DuckDB isolation completely eradicates row-locking / cross-contamination.
- **UNSAFE** - CPU/RAM bounding is unmanaged. The user can dispatch unlimited workers via the UI.

## I. FRONTEND
- **MISSING** - A "Run History" or "Recent Investigations" list on the Landing page.
- **PROVEN** - Execution polling successfully aborts on terminal endpoints.

---

## J. RECOMMENDATION

### Risk Severity
- **Deployment UX:** BLOCKER (Requires Node to run frontend locally)
- **Session Recovery:** MAJOR (Users cannot find completed workflows if they refresh)
- **Storage/Resource:** MAJOR (Unmanaged CSV persistence, hardcoded UI placeholders)

### Recommended C2.5 Scope (Top Priorities)
1. **Unified Deployment Target:** Configure FastAPI to mount and serve the `frontend/dist` directory. This allows the entire CryptoNexus stack to be run via a single `uvicorn` or `python` command without needing Node.js installed on the target machine.
2. **Frontend Run History:** Update `Landing.tsx` to display a list of all existing runs (excluding DEMO_V1) by consuming the existing `GET /runs` paginated endpoint, allowing users to return to active or completed background jobs.
3. **Observability & Cleanup:** 
   - Ensure the API exposes actual case DB row counts (Transactions, Network Obs, Alerts) when in `COMPLETED` state.
   - Update `CommandCenter.tsx` to render these real counts instead of the placeholder `"[DYNAMIC]"`.
   - Add a `os.remove` command post-ingestion to reclaim storage space.

### Explicitly Rejected Scope
- Global Concurrency limits / Celery / Redis. (It's a local desktop-grade tool; we trust the user not to DDoS their own machine, though we should document it).
- Cancellation. OS-level PID killing is out of scope for C2.
- Docker / Kubernetes.

### Exact Acceptance Criteria for C2.5
1. Executing Uvicorn directly successfully serves the React application at `http://127.0.0.1:8000/`.
2. `Landing.tsx` renders a "Recent Investigations" sidebar/list pulling from `/runs`.
3. `CommandCenter.tsx` correctly displays the true transaction and anomaly counts for custom runs.
4. Uploaded CSVs are deleted from `data/runs/<id>/uploads` immediately upon successful ingestion into `raw_records`.

---
**C2.5 RECON STATUS: READY FOR IMPLEMENTATION**
