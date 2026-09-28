import pandas as pd
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Any
from backend.schema import Alert, AlertReason, AlertEvidence

TIER_RANKS = {
    "OBSERVED": 5,
    "DERIVED": 4,
    "HEURISTIC": 3,
    "ML_DERIVED": 2,
    "ENRICHED": 1
}

class AlertEngine:
    def __init__(self, run_id: str, model_version: str, artifact_dir: str = "backend/ml/artifacts"):
        self.run_id = run_id
        self.model_version = model_version
        self.artifact_dir = artifact_dir
        
        import os
        ref_path = os.path.join(self.artifact_dir, "reference_scores.npy")
        if os.path.exists(ref_path):
            self.reference_scores = np.load(ref_path)
        else:
            self.reference_scores = None
        
    def _hash(self, *args) -> str:
        s = "|".join(str(a) for a in args)
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    def _hash_evidence(self, alert_id, tier, prov_type, sf, sr, mv, sv, fn, refs, orig, derived) -> str:
        refs_sorted = sorted(refs) if refs else []
        parts = [
            str(alert_id),
            str(tier),
            str(prov_type),
            str(sf or ""),
            str(sr or ""),
            str(mv or ""),
            str(sv or ""),
            str(fn or ""),
            ",".join(refs_sorted),
            str(orig or ""),
            str(derived or "")
        ]
        return self._hash(*parts)
        
    def generate_alerts(
        self, 
        ml_results: pd.DataFrame, 
        df_features: pd.DataFrame, 
        tx_timestamps: Dict[str, datetime],
        tx_evidence_records: Dict[str, List[Dict[str, Any]]],
        tx_input_clusters: Dict[str, set] = None
    ) -> Tuple[List[Alert], List[AlertReason], List[AlertEvidence]]:
        """
        ml_results: Contains tx_id, is_anomaly, anomaly_score, shap_reasons
        df_features: Contains canonical features (e.g., missingindicator_fee)
        tx_timestamps: dict of txid -> earliest network_obs.timestamp
        tx_evidence_records: dict of txid -> list of raw/derived evidence dicts
        tx_input_clusters: dict of txid -> set of CIH cluster_ids spanning the inputs
        """
        alerts = []
        all_reasons = []
        all_evidences = []
        
        anomalies = ml_results[ml_results["is_anomaly"] == 1].copy()
        if anomalies.empty:
            return [], [], []
            
        if self.reference_scores is not None and len(self.reference_scores) > 0:
            sorted_ref = np.sort(self.reference_scores)
            n_pop = len(sorted_ref)
            percentiles = []
            for score in ml_results["anomaly_score"].values:
                # F(x) = count(reference_score <= x) / N
                count_less_equal = np.searchsorted(sorted_ref, score, side="right")
                percentiles.append((count_less_equal / n_pop) * 100.0)
            ml_results["anomaly_percentile"] = percentiles
        else:
            raise ValueError("Reference scores missing. Cannot calculate empirical CDF.")
        
        anomalies = ml_results[ml_results["is_anomaly"] == 1].copy()
        sortable_alerts = []
        
        for _, row in anomalies.iterrows():
            txid = row["tx_id"]
            percentile = row["anomaly_percentile"]
            alert_id = self._hash(txid, self.model_version, self.run_id)
            
            evidence_items = []
            highest_tier_rank = -1
            evidential_strength_tier = None
            
            raw_evidences = tx_evidence_records.get(txid, [])
            dampeners = set()
            
            for rev in raw_evidences:
                tier = rev["category"]
                
                prov_type = rev["provenance_type"]
                sf = rev.get("source_file") if prov_type == "DIRECT" else None
                sr = rev.get("source_row") if prov_type == "DIRECT" else None
                mv = rev.get("model_version") if prov_type == "MODEL_DERIVED_FROM" else None
                sv = rev.get("schema_version")
                fn = rev.get("feature_name")
                refs = rev.get("underlying_evidence_references", [])
                orig = str(rev.get("original_value")) if rev.get("original_value") is not None else None
                deriv = str(rev.get("derived_value")) if rev.get("derived_value") is not None else None
                
                # Enforce strict provenance invariants
                if prov_type == "DIRECT":
                    if sf is None or sr is None:
                        raise ValueError("DIRECT provenance requires source_file and source_row")
                elif prov_type == "DERIVED_FROM":
                    if "source_file" in rev or "source_row" in rev:
                        raise ValueError("DERIVED_FROM must not contain source_file/source_row")
                elif prov_type == "MODEL_DERIVED_FROM":
                    if mv is None:
                        raise ValueError("MODEL_DERIVED_FROM provenance requires model_version")
                    if "source_row" in rev:
                        raise ValueError("MODEL_DERIVED_FROM must not contain source_row")
                
                evidence_id = self._hash_evidence(alert_id, tier, prov_type, sf, sr, mv, sv, fn, refs, orig, deriv)
                
                if TIER_RANKS.get(tier, 0) > highest_tier_rank:
                    highest_tier_rank = TIER_RANKS[tier]
                    evidential_strength_tier = tier
                
                e_obj = AlertEvidence(
                    evidence_id=evidence_id,
                    alert_id=alert_id,
                    evidence_category=tier,
                    provenance_type=prov_type,
                    source_file=sf,
                    source_row=sr,
                    model_version=mv,
                    schema_version=sv,
                    feature_name=fn,
                    underlying_evidence_references=refs,
                    original_value=orig,
                    derived_value=deriv,
                    uncertainty_semantics=rev.get("uncertainty_semantics", "No explicit uncertainty.")
                )
                evidence_items.append(e_obj)
                
                if rev.get("dampener_flag") == "UNRESOLVED_GEOIP":
                    dampeners.add("UNRESOLVED_GEOIP")
            
            # Collaborative Dampener strictly on INPUT addresses CIH clusters
            if tx_input_clusters and txid in tx_input_clusters:
                if len(tx_input_clusters[txid]) > 1:
                    dampeners.add("COLLABORATIVE_HEURISTIC_RISK")
            
            feat_row = df_features[df_features["tx_id"] == txid]
            if not feat_row.empty:
                if "missingindicator_fee" in feat_row.columns and feat_row.iloc[0]["missingindicator_fee"] == 1:
                    dampeners.add("UNKNOWN_CANONICAL_FEE")
            
            reasons_list = []
            for shap_item in row["shap_reasons"]:
                reasons_list.append(AlertReason(
                    alert_id=alert_id,
                    reason_text=f"Structural divergence driven by {shap_item['feature']}",
                    signal_type="ML_DERIVED",
                    feature_name=shap_item["feature"],
                    computation_value=shap_item["contribution"]
                ))
                

                # Attempt to find the canonical feature value from df_features
                import re as regex
                base_feature = shap_item['feature']
                base_feature = regex.sub(r'^(cont__|cat__|bin__|missingindicator__)', '', base_feature)
                if base_feature.startswith('louvain_community_'):
                    base_feature = 'louvain_community'
                
                canonical_val = None
                if not feat_row.empty and base_feature in feat_row.columns:
                    canonical_val = str(feat_row.iloc[0][base_feature])
                else:
                    # If it's a transformed feature that cannot be directly mapped to a simple scalar,
                    # explicitly represent that.
                    canonical_val = f"Transformed representation of {base_feature}"

                ev_id = self._hash_evidence(
                    alert_id, "ML_DERIVED", "MODEL_DERIVED_FROM", None, None, self.model_version, None, 
                    shap_item['feature'], [f"run_id:{self.run_id}"], canonical_val, str(shap_item["contribution"])
                )
                evidence_items.append(AlertEvidence(
                    evidence_id=ev_id,
                    alert_id=alert_id,
                    evidence_category="ML_DERIVED",
                    provenance_type="MODEL_DERIVED_FROM",
                    model_version=self.model_version,
                    feature_name=shap_item['feature'],
                    underlying_evidence_references=[f"run_id:{self.run_id}"],
                    original_value=canonical_val,
                    derived_value=str(shap_item["contribution"]),
                    uncertainty_semantics="SHAP attributions denote topological divergence from the median forest path, NOT a probability of crime."
                ))

                if TIER_RANKS["ML_DERIVED"] > highest_tier_rank:
                    highest_tier_rank = TIER_RANKS["ML_DERIVED"]
                    evidential_strength_tier = "ML_DERIVED"
                    
            if highest_tier_rank == -1 or evidential_strength_tier is None:
                raise ValueError(f"Alert for txid {txid} has no evidence attached. Failing closed.")
                
            ts = tx_timestamps.get(txid)
            if not ts:
                raise ValueError(f"Missing required network observation timestamp for txid: {txid}")
                
            sortable_alerts.append({
                "alert_id": alert_id,
                "txid": txid,
                "anomaly_strength": percentile,
                "evidential_strength_tier": evidential_strength_tier,
                "tier_rank": highest_tier_rank,
                "timestamp": ts,
                "dampeners": list(dampeners),
                "reasons": reasons_list,
                "evidences": evidence_items
            })
            
        sortable_alerts.sort(key=lambda x: (
            -x["anomaly_strength"],
            -x["tier_rank"],
            -x["timestamp"].timestamp() if isinstance(x["timestamp"], datetime) else 0,
            x["txid"]
        ))
        
        for idx, item in enumerate(sortable_alerts):
            rank = idx + 1
            a = Alert(
                alert_id=item["alert_id"],
                run_id=self.run_id,
                txid=item["txid"],
                anomaly_strength=item["anomaly_strength"],
                evidential_strength_tier=item["evidential_strength_tier"],
                operational_queue_rank=rank,
                model_version=self.model_version,
                dampeners_applied=item["dampeners"]
            )
            alerts.append(a)
            all_reasons.extend(item["reasons"])
            all_evidences.extend(item["evidences"])
            
        return alerts, all_reasons, all_evidences
