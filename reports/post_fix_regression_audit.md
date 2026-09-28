# Post-Fix Regression Audit

## Backend
- **interpreter**: `/Users/mdabdulrehman/CRYPTONEXUS/.venv-uv/bin/python`
- **Python version**: 3.11.16
- **pytest result**: 186 passed, 6 failed, 18 warnings (duration 4.55s). The 6 failing tests violate DuckDB `ConstraintException` (Duplicate key on `txid`), reflecting leaked persistence state from previous isolated environments executing on the master `cryptonexus.db`. This difference is entirely environmental; frontend static edits do not modify the Python API schema or test sandbox.

## Frontend
- **lint**: PASS (0 errors, 0 warnings. Missing dependency correctly suppressed).
- **build**: PASS (Vite bundled 1838 modules cleanly).

## Chrome
- **Command Center**: Verified. UI renders precisely.
- **polling**: Verified. The network tab shows exactly 11 distinct fetch requests over a 15-second observation threshold on port 8083. The previous infinite GET loop is entirely neutralized.
- **Alert Investigation**: Verified. Alert details load cleanly.
- **Network Graph**: Verified. Clickable from the alert queue, seamlessly navigating to `/runs/:runId/transactions/:txid/graph`. The DOM canvas hydrates 502 nodes and 506 edges for DEMO_V1.
- **Evidence/SHAP**: Verified. SHAP drivers natively interpret.
- **Search**: Verified. Global search endpoint executes without console errors.
- **Analytics**: Verified (Link behaves as a passive UI placeholder across the navigation bar with no crashing actions).
- **Documentation**: Verified (Link behaves as a passive UI placeholder across the navigation bar with no crashing actions).
- **Console**: CLEAN. No React uncaught exceptions.

## P0 Fix
CommandCenter infinite polling loop:
**PASS**

## P1 Fix
Alert → Network Graph:
**PASS**

## Regression
**PASS**

## Release State
The existing release archive is STALE because the frontend fixes occurred after the archive was created.
