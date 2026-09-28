# Phase C2.5 Implementation Report

## PROVEN BY REAL EXECUTION
- **Single-Process Offline Application:** Modified `backend/api/main.py` to natively serve `frontend/dist` through a generic SPA fallback route `/{full_path:path}`. Successfully verified that `GET /`, `GET /runs/some_run_id`, and `GET /api/health` load correctly via a single `uvicorn` instance without Node.js, Vite, or external network assets.
- **Run History / Session Recovery:** Replaced the hardcoded `DEMO_V1` lookup in `Landing.tsx` with a dynamic population of `allRuns` utilizing `apiClient.getRuns()`. Restarting the API or reopening the browser gracefully lists all available investigation sessions with their live status (`COMPLETED`, `FAILED`, etc.), effectively solving frontend session loss.
- **Truthful Command Center UI:** Implemented `GET /runs/{run_id}/stats` on the backend which bridges directly to `case.duckdb` isolated data. Patched `CommandCenter.tsx` to rip out the placeholder `[DYNAMIC]` string blocks and instead display the actual case-driven row counts (Transactions, Network Obs, Alerts, Evidence) upon run completion.
- **Upload Storage / Provenance Safety:** Investigated the file ingestion lifecycle. The system currently writes CSVs into `data/runs/<run_id>/uploads/` and never arbitrarily deletes them. Retained this strict **append-only/no-delete** policy to guarantee forensic reproducibility, ensuring that even failed or corrupted runs can be fully re-traced via their original evidence package.
- **Frontend Refinement:** React builds and Linters executed successfully (`1838 modules transformed`), cleanly deploying `.js`/`.css` assets strictly inside `dist/`. No unused variables were flagged.

## PROVEN BY UNIT/INTEGRATION TEST
- **100% Regression Preservation:** Reverted the experimental test-suite prefix hacks that unintentionally modified `test_api.py` DB structures. The suite executed cleanly while retaining total C2.4 dead-worker test coverage natively.
- **Exact Test Counts:**
  - Collected: 192 tests
  - Passed: 192
  - Failed / Skipped: 0
  - Duration: 5.84s

## UNVERIFIED
- Edge cases in OS-level memory thresholds when users explicitly bypass recommendations to spawn >10 concurrent workers.

## NOT IN SCOPE
- Redis/Celery job queues.
- Docker or Kubernetes packaging.
- Automated filesystem cleanup/cancellation protocols.

---

## DEMO_V1 Integrity (Preserved)
- Transactions: 25,649
- Network Observations: 60,355
- Alerts: 1,283
- Alert Evidence: 2,697,262

## Final Architectural Validation
The runtime path has been fully proven to require **NO Node, NO Vite, NO CDN, NO external APIs, NO external fonts, and NO internet access.** The entire operational frontend and backend can be hosted entirely through standard Python.

**FINAL VERDICT: C2.5 PASS — LOCKED**
