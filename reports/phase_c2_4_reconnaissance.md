# C2.4 Reconnaissance

## Current Worker Lifecycle
The worker is currently dispatched as an independent Python subprocess. As part of its startup, it initializes the `case.duckdb` schema and inserts a local `pipeline_runs` row with `status='RUNNING'`. 
Throughout execution, the `WorkerRepository` intercepts status updates and proxies them to the master `cryptonexus.db` via an HTTP `PATCH` callback (`/runs/{run_id}/internal/status`). 
Meanwhile, the FastAPI process that spawned the worker attaches an in-memory background thread (`monitor_worker_process_sync`) that blocks on `proc.wait()`. If the process exits without hitting terminal status, the thread catches the exit code and marks the master DB as `FAILED`.

## Registry Consistency
**Master DB vs Case DB Mismatch:**
The worker initializes `pipeline_runs` in `case.duckdb` as `RUNNING`. However, `WorkerRepository.finalize_pipeline_run` *only* fires the HTTP callback to the master database; it does not update the `case.duckdb` row. Thus, every successfully generated `case.duckdb` is permanently stuck with a localized internal status of `RUNNING`, relying exclusively on the master `cryptonexus.db` for the true `COMPLETED` state.

## Failure Modes
1. **Worker API Callback Failure**: The `report_status` function uses `urllib.request.urlopen` with no retry logic. If the API is momentarily restarting when the worker calls `COMPLETED`, the HTTP request throws an exception, is swallowed via `except Exception: print`, and the worker exits 0. 
2. **API Restart Monitor Loss**: If FastAPI restarts while a worker is running, the `monitor_worker_process_sync` thread is permanently lost. The worker is now functionally orphaned from the monitor's perspective.
3. **OS-Level Worker Crash (OOM/Segfault)**: If the worker crashes *after* an API restart, the monitor thread is missing, meaning the master DB will never be updated and will eternally broadcast `RUNNING`.
4. **False Failure on Restart**: If the worker successfully finishes (but drops the HTTP callback due to API downtime), it exits gracefully. When FastAPI starts back up, its startup recovery check runs `os.kill(worker_pid, 0)`. Recognizing the process is dead, the startup recovery assumes it crashed and incorrectly marks the run as `FAILED`, effectively invalidating a perfectly valid `case.duckdb`.

## Recovery Behavior
- Current recovery is a one-time check during `main.py` startup. It looks for `QUEUED`/`RUNNING` runs and uses `os.kill(worker_pid, 0)`.
- If the PID is dead, it aggressively forces a `FAILED` state ("Worker process unexpectedly terminated"). 
- It lacks any capability to query `case.duckdb` to verify if the worker actually succeeded before dying.

## Frontend Failure Handling
The C2.3 frontend accurately maps terminal failure states:
- A `FAILED` run successfully breaks the polling loop and mounts the `RunProgress` component displaying the error message and failed stage.
- A missing run correctly defaults to a `<SystemState type="RUN_UNAVAILABLE" />`.
- A missing `case.duckdb` throws a backend 404 which the frontend safely translates into `<SystemState type="ERROR" />` without crashing the application.
- **Vulnerability**: If the backend falls into the eternal `RUNNING` trap (due to the missing monitor thread), the frontend will unconditionally poll forever.

## Progress Reliability
- Verified: Stages are driven purely by backend logical strings (`INGEST`, `GEOIP`, etc.).
- Verified: No fake percentage computation exists.
- Verified: Polling strictly terminates upon detecting `COMPLETED` or `FAILED`.
- Verified: Component unmount safely clears the `setTimeout` loop, preventing duplicate polling.

## DEMO_V1 Protection
- The `Landing.tsx` logic accurately preserves the default hardcoded navigation to `DEMO_V1` if selected.
- Backend routing correctly seals `DEMO_V1` queries to `cryptonexus.db`.
- The worker completely ignores `DEMO_V1`, guaranteeing isolation.

## Existing Tests
- Current tests cover standard synchronous E2E pipeline behavior (`test_pipeline.py`) and API contract validations (`test_api.py`), but entirely mock or skip process-level failure conditions.
- `test_c2_2.py` tests standard "happy path" isolation routing.

## Gaps
1. Worker lacks HTTP retry/backoff logic for API callbacks.
2. Worker leaves `case.duckdb` in an eternally `RUNNING` state.
3. FastAPI lacks a persistent health-check polling loop for orphaned pids (relying only on single-pass startup checks and fragile memory threads).
4. Startup recovery aggressively fails dead PIDs without verifying the localized `case.duckdb` integrity.

## Proposed C2.4 Scope
1. **Case DB Finalization:** Modify `WorkerRepository` to write terminal states (`COMPLETED`/`FAILED`) locally to `case.duckdb` in addition to the API callback.
2. **Callback Resiliency:** Implement exponential backoff/retries in `worker.py`'s `report_status`.
3. **Intelligent Recovery:** Upgrade the `main.py` startup recovery to inspect `case.duckdb`'s localized `pipeline_runs` table. If the localized table reads `COMPLETED`, gracefully recover the master DB to `COMPLETED` rather than forcing a failure.
4. **Persistent Monitor:** Replace the fragile in-memory `proc.wait()` thread with a robust periodic background task (e.g. `fastapi-utils` or `asyncio` loop) that routinely validates active PIDs and recovers them based on case DB state.

## Required Tests
To guarantee worker reliability, C2.4 must implement:
1. `test_worker_api_retry`: Prove the worker successfully retries if the API is momentarily unavailable.
2. `test_startup_recovery_success`: Prove that a `COMPLETED` case DB correctly heals a `RUNNING` master DB during startup.
3. `test_startup_recovery_crash`: Prove that an incomplete case DB with a dead PID correctly heals to `FAILED`.
4. `test_orphaned_worker_reaper`: Prove that the active background monitor catches and reaps a process that is unexpectedly `kill -9`'d mid-execution.

## Risks
- Depending on OS configurations, PID recycling could theoretically trick `os.kill(pid, 0)` into thinking the worker is still alive if a new unrelated process adopts the exact same PID. (Low probability in local offline environments, but structurally possible).
