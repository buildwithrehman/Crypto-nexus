# Phase 18.4 Semantic Audit

## 1. SHAP Semantic Chain
- **IsolationForest decision_function**: Outputs an anomaly score for each transaction. Lower (more negative) values indicate structural outliers compared to the median forest path.
- **anomaly_score**: Inverts `decision_function` (via `anomaly_score = -decision_function`) such that *higher* positive scores intuitively represent greater anomaly severity.
- **SHAP values**: Computed on the `IsolationForest`. A negative SHAP value pulls the `decision_function` lower (more negative). Since our `anomaly_score` is inverted, a negative SHAP value *increases* the anomaly severity.
- **Driver ordering**: Top drivers are strictly extracted by picking the most negative SHAP features (`np.argsort(instance_shap)[:3]`), confirming that the reported reasons strictly list the features causing the transaction to be anomalous.
- **Direction Fix**: The direction string was previously outputting `"negative"`, which could mislead users into thinking the feature decreased the anomaly score. This was fixed to read `"increases anomaly"` for negative SHAP values, accurately reflecting its contribution to `anomaly_strength`.

## 2. Driver Ordering Verification
Verified. `np.argsort` correctly identifies the largest negative SHAP values that drove the sample into the outlier regions of the IsolationForest.

## 3. Transformed-Feature Mapping Verification
**Issue Found**: Initially, transformed pipeline feature names (e.g., `cat__louvain_community_11`) were improperly used to query raw feature values. Since `ML_DERIVED` artifacts incorrectly stored the SHAP score in `derived_value` (throwing away the canonical value), the report showed SHAP values in place of actual feature values.
**Fix Implemented**: Modified `backend/scoring/alerts.py` to extract the base canonical feature name (stripping `cont__`, `cat__`, `bin__`), query the original `df_features` dataframe provided by the `PipelineOrchestrator`, and insert the canonical scalar directly into the `original_value` of the `AlertEvidence` artifact. The interpreter was updated to correctly extract this canonical `original_value`. The report now accurately shows distinct canonical values (e.g., `value 32.0` -> `shap -1.0345`).

## 4. Evidence-Tier Verification
Verified. The explanations correctly maintain the existing constraints: `OBSERVED`, `DERIVED`, `HEURISTIC`, `ML_DERIVED`, and `ENRICHED`. No arbitrary probability or numeric confidence scoring was introduced.

## 5. Caveat Verification
Verified. The interpreter dynamically attaches the following constraints from authoritative state data without text matching fragility:
- "Anomaly indicates structural rarity, not criminality."
- "Network observation does not establish IP ownership."
- "Exact UTXO lineage cannot be established without prev_txid/prev_vout fields."
- Dynamic caveats correctly flag missing `UNKNOWN_CANONICAL_FEE`, `UNRESOLVED_GEOIP`, and `COLLABORATIVE_HEURISTIC_RISK` directly from the `dampeners_applied` array set by the `AlertEngine`.

## 6. Provenance Verification
Verified. Traceability remains intact. Direct observations retain `source_file` and `source_row` without synthesizing rows for `ML_DERIVED` features (which correctly list `run_id` as their underlying reference). Cross-run leakage is prevented because `QueryService` inherently filters all joins by `run_id` and `txid`.

## 7. Determinism Verification
Verified. `run_audit.py` (which executed dual isolated pipeline runs) confirmed bit-for-bit equivalence in feature sums, variances, anomaly outputs, and SHAP distributions given deterministic random states and dataset preservation.

## 8. API Contract Verification
Verified. Tested in `tests/test_api_explanation.py` and via OpenAPI schema matching. The explanation properties strictly append to the existing backward-compatible REST models (`AlertDetail`, `TransactionInvestigationResponse`).

## Final JSON Frontend Contract Example
```json
{
  "alert_id": "a6f1d2...",
  "txid": "c2d66154d82a...",
  "anomaly_strength": 99.75,
  "summary": "This transaction is structurally unusual relative to the model reference population. The strongest model contributors were louvain_community, unique_ip_propagators, and propagation_edge_count.",
  "key_drivers": [
    {
      "feature": "louvain_community",
      "value": 14.0,
      "shap_value": -1.2210,
      "direction": "increases anomaly",
      "meaning": "Topological cluster assignment identifying distinct network communities.",
      "evidence_tier": "ML_DERIVED"
    }
  ],
  "investigation_caveats": [
    "Anomaly indicates structural rarity, not criminality.",
    "Network observation does not establish IP ownership.",
    "GeoIP enrichment is unavailable in this run.",
    "Exact UTXO lineage cannot be established without prev_txid/prev_vout fields."
  ],
  "provenance": [
    "data/demo_v1/network/observations.csv:424",
    "data/demo_v1/network/observations.csv:422"
  ],
  "human_readable_lead": "STRUCTURAL ANOMALY\n\nTransaction:\n    c2d66..."
}
```

## Verdict
READY FOR PHASE 19 FRONTEND
