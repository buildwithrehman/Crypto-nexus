# Phase 17.1 — End-to-End Orchestrator

## Pipeline Lifecycle

The pipeline orchestrates the progression of raw data through the following conceptual stages:
1. **INGEST:** Parses and loads raw source files into the DuckDB relational repository.
2. **GEOIP:** Unresolved network observations are enriched with geographical and ASN context.
3. **CORRELATION & CIH:** Pairwise deterministic evaluations construct topological clusters.
4. **GRAPH:** The base canonical transaction graph is built, properly scoped to the run.
5. **GRAPH ANALYSIS & FEATURES:** Generates deterministic structural metrics (Centrality, Degrees, Temporal).
6. **ML SCORING:** In inference mode, scores transactions against verified baseline artifacts. In training mode, artifacts are persisted.
7. **ALERTS:** Aggregates raw observations, heuristical evidence, and ML anomalies into semantic Alerts.

## Run Isolation

To guarantee offline determinism and safe concurrent processing, every SQL query extracting domain intelligence is strictly scoped to `run_id = ?` where the schema permits (e.g., `network_obs`, `transactions`, `clustering_evidence`). 
The topological graph is restricted only to nodes and edges originating directly from the specified run context. Historical noise or data from parallel ingestion jobs cannot contaminate the feature engineering process.

## ML Artifact Lifecycle

Ordinary scoring runs (inference mode) are strictly stateless regarding model artifacts. They load:
- `preprocessor.joblib`
- `isolation_forest.joblib`
- `hdbscan.joblib`
- `metadata.json`
- `reference_scores.npy`

Inference operates exclusively on these locked files to preserve deterministic empirical CDF validation. They are never overwritten by an inference run. Training runs are a distinct operational configuration explicitly triggered via `is_training_run`.

## Failure Semantics

The orchestrator operates with fail-closed semantics. It does not swallow algorithmic or integrity exceptions. A failure at any downstream stage immediately halts the pipeline, logs the exact exception, and propagates the failure to the caller. 
If an artifact is missing during an inference run, it crashes immediately rather than defaulting or retraining inline.

## Offline Guarantees
- Local MaxMind MMDB for GeoIP.
- Local SQLite/DuckDB persistence.
- Zero external APIs or cloud offloading.
