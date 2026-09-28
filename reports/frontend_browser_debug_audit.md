# Browser Runtime Debug Audit

## Environment
- OS: macOS (ARM64)
- Chrome version: Chrome DevTools MCP Client
- URL: `http://127.0.0.1:8082`
- port: 8082
- release directory: `/Users/mdabdulrehman/CRYPTONEXUS_RELEASE_SMOKE_TEST`

## Console Errors
Table:

| Error | File | Line | Root Cause | Impact |
| --- | --- | --- | --- | --- |
| None | N/A | N/A | React errors caught by boundaries or unmounted without trace for bad routes. | Masked visibility of routing mismatch. |

## Network Failures
Table:

| Method | URL | Status | Response | Root Cause |
| --- | --- | --- | --- | --- |
| GET | `/api/runs/...` | 200 | OK | (Infinite loop) Component re-render continually requests identical endpoints over 1,000s of times, though HTTP status is 200. |

## Broken Screens
Table:

| Screen | Expected | Actual | Root Cause |
| --- | --- | --- | --- |
| `CommandCenter` (`/runs/:runId`) | Page loads once and idles | Infinite polling loop generating thousands of requests per minute | `run` state variable included in `useEffect` dependency array, triggering continuous re-evaluation when `setLocalRun` updates object reference. |
| `AlertInvestigation` -> Graph Link | Navigation to `NetworkGraph` | Navigates to `EvidenceProvenance` | Link uses `/provenance` route explicitly instead of `/graph` in `<Link to="...">`. |

## API Contract Issues
List exact mismatches:
- None. `PaginatedResponse` vs Object expectations are correctly adhered to across the UI. Stats payload conforms accurately.

## Static Asset Issues
List exact failures:
- None. JS bundles, CSS files, WOFF2 fonts, and `logo.png` return 200 OK without MIME type violations.

## Graph Issues
List exact failures:
- Network Graph fails to load *only* if the URL pattern `/runs/:runId/graph` is manually invoked because `App.tsx` requires `/runs/:runId/transactions/:txid/graph`. 
- When invoked via the correct parameterized URL pattern, Graph topology loads flawlessly (Node count: 502, Edge count: 506).

## Root Causes
Separate:
- **P0** — `CommandCenter.tsx` infinite request loop (`run` state variable passed into `loadData`'s `useEffect` dependency array triggering cyclic API saturation).
- **P1** — `AlertInvestigation.tsx` contains an incorrect `Link` destination for "NETWORK GRAPH" (`to={\`/runs/${runId}/alerts/${alertId}/provenance\`}`).
- **P2** — Cosmetic source attribution (`CommandCenter` hardcodes `runId === 'DEMO_V1'` instead of evaluating the `run.is_demo` flag).
- **P3** — None.

## Recommended Fixes
1. **P0 Fix:** In `CommandCenter.tsx`, remove `run` from the `useEffect` dependency array:
   ```tsx
   // Change:
   // }, [runId, setRun, run]);
   // To:
   // }, [runId, setRun]);
   ```
2. **P1 Fix:** In `AlertInvestigation.tsx`, correct the Graph link destination:
   ```tsx
   // Change:
   // to={`/runs/${runId}/alerts/${alertId}/provenance`}
   // To:
   // to={`/runs/${runId}/transactions/${alert.txid}/graph`}
   ```

## Fix Applied

### P0 — CommandCenter polling loop
- **file:** `frontend/src/pages/CommandCenter.tsx`
- **root cause:** The `run` state variable was included in the `useEffect` dependency array. When the effect resolved, `setLocalRun(runData)` created a new object reference, triggering the dependency array to restart the effect, resulting in an infinite API GET loop.
- **exact fix:** Removed `run` from the dependency array, changing `[runId, setRun, run]` to `[runId, setRun]`, and added `// eslint-disable-next-line react-hooks/exhaustive-deps` to preserve correct lifecycle polling behavior.
- **validation result:** Verified via Chrome DevTools. `CommandCenter` now loads correctly, polls precisely via `setTimeout`, and stabilizes once the run is complete. The infinite GET request storm has been resolved (request count dropped from 1,000+ to ~11).

### P1 — Alert Network Graph navigation
- **file:** `frontend/src/pages/AlertInvestigation.tsx`
- **root cause:** A copy-paste error where the `<Link to...>` destination for "NETWORK GRAPH" explicitly referenced the `provenance` route instead of the parameterized `graph` route.
- **exact fix:** Modified line 432: changed `to={\`/runs/${runId}/alerts/${alertId}/provenance\`}` to `to={\`/runs/${runId}/transactions/${alert.txid}/graph\`}`.
- **validation result:** Verified via Chrome DevTools. The "NETWORK GRAPH" button correctly anchors to the exact URL format defined in `App.tsx` (`/runs/:runId/transactions/:txid/graph`). Clicking it successfully loads the graph component without routing errors.

### Regression
- **lint:** PASS (`npm run lint` reported 0 errors, 0 warnings).
- **build:** PASS (Vite production build succeeded).
- **browser console:** PASS (No React unmounts or silent exceptions).
- **network polling:** PASS (Fixed loop; stable network activity).
- **graph navigation:** PASS (Graph loads 502 nodes and 506 edges correctly based on valid URL).
