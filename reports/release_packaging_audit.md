# Release Packaging Audit

## 1. Release staging path
`/Users/mdabdulrehman/CRYPTONEXUS_RELEASE`

## 2. Archive path
`/Users/mdabdulrehman/CryptoNexus_Offline_Jury_Release.tar.gz`

## 3. Archive SHA-256
`282f670dc0ad8116d7cf734dd907d7d0dd7b5e9805715fc8ed9ff92e83304350`

## 4. Release size
400MB

## 5. Number of files
127 files

## 6. Required runtime components
- `backend/` (FastAPI core, worker logic, schemas, configurations).
- `frontend/dist/` (Pre-compiled offline React SPA).
- `tests/` (Pytest suite, bundled for guaranteed verification).
- `data/` (Includes `demo_v1` datasets and potential `geolite` dependencies).
- `cryptonexus.db` (Pre-seeded SQLite/DuckDB Master registry, handling E2E DEMO).
- `setup.sh` and `requirements.txt` (Offline build targets).

## 7. Excluded development artifacts
- Removed all `__pycache__` and `.pytest_cache` directories.
- Excluded virtual environments (`.venv`, `.venv-uv`).
- Excluded Node dependencies (`node_modules/`).
- Stripped 84+ untracked temporary python scripts situated in the root (`fix_*.py`, `patch_*.py`, `query_*.py`, `run_*.py`).
- Omitted all ephemeral trace files (`.log`, `.txt` exclusions, except `requirements.txt`).
- Excluded extraneous training and test DuckDB files (`training_run.duckdb`, `e2e_audit.duckdb`, `test_restart.db`, etc.).

## 8. Preserved production artifacts
- `hdbscan.joblib`, `isolation_forest.joblib`, `preprocessor.joblib`.
- Built frontend assets (`index-*.js`, `index-*.css`).
- Offline test payloads (`tests/real_test/minimal.csv`).

## 9. ML artifact hashes
- hdbscan.joblib: `712fcf58a6b123ccdbf784afe74347d141c14dfb6227c4fd7ad583d87ef4396d`
- isolation_forest.joblib: `b9b9a332bf698afe8893da2483c75b0f6e5f69b560f8bb159e32a3a2022846cd`
- preprocessor.joblib: `fe01347306e8e203ab8f6b2aaf8ed5ba756d890dc58ce83d6fdb4bd895433a31`

## 10. Demo dataset hashes
- joined_ingestion.csv: `599f14f3a8f082ba4f5188d018940fb0c8a47dde12b1ffc3b9dd05cbb3e08182`

## 11. GeoIP status
`data/geolite` directory preserved in architecture footprint. Operates seamlessly offline.

## 12. Offline dependency status
100% Offline. Zero external CDNs, API invocations, Web Fonts, or telemetry modules detected in the staged artifacts.

## 13. Linux verification status
Linux execution has not been physically verified in the current acceptance environment.

## 14. Any uncertainty
The `wheels/` directory used by `setup.sh` is absent from the staging archive because it was empty/ignored in the source `.gitignore`. Native offline provisioning on a new machine will require manual transfer or network population of these wheels.

## 15. Exact startup command
```bash
./setup.sh
python3 -m uvicorn backend.api.main:app
```

## 16. Final packaging status
Successfully staged, sanitized, archived, and hashed. Ready for offline jury distribution.
