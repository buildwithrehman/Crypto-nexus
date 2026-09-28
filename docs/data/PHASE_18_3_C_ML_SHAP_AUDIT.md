# Phase 18.3-C ML & SHAP Audit

## Executive Summary
The full pipeline execution of the CryptoNexus architecture (Phase 1-17) successfully processed the relational demo dataset. This execution correctly integrated the 25,649 transactions with their 60,355 corresponding network observations without flattening, retaining referential integrity, and accurately scoping network propagation events to the canonical TXIDs.

The resulting Isolation Forest model correctly detected structural anomalies without relying on explicitly defined criminal typologies, interpreting anomalous behavior purely through mathematical variance (anomaly_strength) across the reference population. The SHAP explanation layer effectively extracted the top deterministic drivers, and the evidence engine traced every driver back to its source provenance without hallucinating evidence.

## Dataset Used
- **Transactions**: `data/demo_v1/blockchain/transactions.csv` (25,649 records)
- **Observations**: `data/demo_v1/network/observations.csv` (60,355 records)

## Stage Counts
- **INGEST**: 25,649 Transactions accepted, 60,355 Network Observations accepted.
- **GEOIP**: Skipped. `GEOIP_VALIDATION_PENDING` properly respected; pipeline mocked this single stage successfully to allow downstream evaluation.
- **CORRELATION / CIH**: 25,649 transactions correlated.
- **GRAPH**: 25,649 transactions evaluated.
- **FEATURES**: 25,649 feature rows generated.
- **ALERTS**: 1,283 alerts generated (exactly matching `is_anomaly` count).

## Feature Statistics
Exactly 17 canonical Phase 14 features were fed into the Isolation Forest:
`in_degree`, `out_degree`, `total_degree`, `betweenness`, `louvain_community`, `is_peel_chain`, `weighted_in_degree`, `weighted_out_degree`, `weighted_total_degree`, `fee`, `average_input_value`, `average_output_value`, `unique_in_addresses`, `unique_out_addresses`, `unique_ip_propagators`, `propagation_edge_count`, `duration_active_seconds`

Network Feature Variance:
- `unique_ip_propagators`: Variance > 0 (Min: 1, Max: 8)
- `propagation_edge_count`: Variance > 0 (Min: 1, Max: 8)
- `duration_active_seconds`: Variance > 0 (Min: 0, Max: 600)

## Isolation Forest Results
- **Total Transactions Analyzed**: 25,649
- **Anomalies Detected**: 1,283 (approx 5% contamination target)
- **Anomaly Strength**: Measured strictly as empirical CDF (0.0 to 100.0) relative to the reference population's decision function. No reinterpretation into "probability of crime" occurred.

## HDBSCAN Results
HDBSCAN successfully processed the canonical feature space, delineating topological sub-clusters. No semantic labels (e.g., "fraud ring") were forcibly assigned to these structural clusters.

## SHAP Results & Top SHAP Drivers
For every anomalous transaction, SHAP successfully extracted absolute contribution magnitude per feature.
- Top drivers included `duration_active_seconds` and `propagation_edge_count` for structurally unusual network propagation.
- SHAP values were finite, and the canonical features mapped cleanly to the drivers. No hallucinated/manual suspicious features were appended.

## Alert/Evidence Audit
- **Alert Count**: 1,283 (Matches anomaly count exactly).
- **Evidence Count**: >10,000 evidence artifacts accurately trace the lineage.
- **Provenance**: `MODEL_DERIVED` evidence points directly to the `model_version`, while `DIRECT` evidence traces back to exact `source_row` line numbers in the relational `.csv` files.
- **Cross-run Leakage**: 0.

## Determinism
Pipeline was executed twice. Feature counts, alert counts, and SHAP top-3 orderings were 100% deterministic between Run 1 and Run 2.

## Dataset Immutability
`shasum` of both source files perfectly matches pre-execution hashes:
- `e11b0b01126f1d60a17f0dc52003b8748787f539  transactions.csv`
- `5904eb86605b9a854ad1af68d93d1250559ac22a  observations.csv`

## Human Explanation Readiness
1. **Can CryptoNexus identify anomalous transactions without manual suspicion rules?** YES (via IF empirical variance).
2. **Can the system identify the strongest model contributors using SHAP?** YES.
3. **Can each contributor be mapped to a defined feature meaning?** YES.
4. **Can each feature be traced back to underlying evidence?** YES.
5. **Can each alert be traced to source/provenance?** YES.
6. **Are explanations distinguishable by evidence tier?** YES.
7. **Are investigation caveats preserved?** YES.
8. **Can a future explanation layer generate a human-readable lead without inventing evidence?** YES (the extracted `audit_alerts_prototype.json` payload proves the structured data is sufficient).

## Final Verdict
**READY FOR 18.4 — EVIDENCE INTERPRETATION LAYER**
