import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.schema import Alert, AlertReason, AlertEvidence

FEATURE_METADATA = {
    "in_degree": {
        "meaning": "Number of unique addresses providing inputs to this transaction.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "out_degree": {
        "meaning": "Number of unique addresses receiving outputs from this transaction.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "total_degree": {
        "meaning": "Total number of unique addresses involved as inputs or outputs.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "betweenness": {
        "meaning": "Structural centrality within the local transaction subgraph.",
        "evidence_tier": "ML_DERIVED",
        "domain": "GRAPH"
    },
    "louvain_community": {
        "meaning": "Topological cluster assignment identifying distinct network communities.",
        "evidence_tier": "ML_DERIVED",
        "domain": "GRAPH"
    },
    "is_peel_chain": {
        "meaning": "Pattern consistent with a peel-chain distribution hypothesis.",
        "evidence_tier": "HEURISTIC",
        "domain": "GRAPH"
    },
    "weighted_in_degree": {
        "meaning": "Sum of incoming value traversing into this transaction.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "weighted_out_degree": {
        "meaning": "Sum of outgoing value traversing from this transaction.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "weighted_total_degree": {
        "meaning": "Total value volume processed through this transaction.",
        "evidence_tier": "DERIVED",
        "domain": "GRAPH"
    },
    "fee": {
        "meaning": "Network fee explicitly attached to this transaction.",
        "evidence_tier": "OBSERVED",
        "domain": "TRANSACTION"
    },
    "average_input_value": {
        "meaning": "Average value of inputs consumed.",
        "evidence_tier": "DERIVED",
        "domain": "TRANSACTION"
    },
    "average_output_value": {
        "meaning": "Average value of outputs generated.",
        "evidence_tier": "DERIVED",
        "domain": "TRANSACTION"
    },
    "unique_in_addresses": {
        "meaning": "Count of distinct input addresses.",
        "evidence_tier": "DERIVED",
        "domain": "TRANSACTION"
    },
    "unique_out_addresses": {
        "meaning": "Count of distinct output addresses.",
        "evidence_tier": "DERIVED",
        "domain": "TRANSACTION"
    },
    "unique_ip_propagators": {
        "meaning": "Number of distinct peer IP addresses through which the transaction was observed.",
        "evidence_tier": "DERIVED",
        "domain": "NETWORK"
    },
    "propagation_edge_count": {
        "meaning": "Total number of network peer-to-peer propagation events recorded.",
        "evidence_tier": "DERIVED",
        "domain": "NETWORK"
    },
    "duration_active_seconds": {
        "meaning": "Time span over which network propagation observations occurred.",
        "evidence_tier": "DERIVED",
        "domain": "NETWORK"
    }
}

class EvidenceInterpreter:
    @staticmethod
    def generate_explanation(
        alert: Any, 
        reasons: List[Any], 
        evidences: List[Any],
        tx_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a structured human-readable explanation object for an alert.
        """
        
        # 1. SHAP Interpretation
        # Sort reasons by absolute SHAP magnitude descending
        sorted_reasons = sorted(reasons, key=lambda r: abs(float(r.computation_value)), reverse=True)
        top_drivers = []
        for r in sorted_reasons[:3]:
            raw_feat_name = r.feature_name
            # strip prefixes like cont__, cat__, missingindicator__
            feat_name = re.sub(r'^(cont__|cat__|bin__|missingindicator__)', '', raw_feat_name)
            # strip trailing categorical cluster ID (e.g. louvain_community_11 -> louvain_community)
            if feat_name.startswith('louvain_community_'):
                feat_name = 'louvain_community'
                
            meta = FEATURE_METADATA.get(feat_name, {
                "meaning": "Unknown feature.",
                "evidence_tier": "UNKNOWN",
                "domain": "UNKNOWN"
            })
            
            # Find the actual feature value in evidence
            # Looking for evidence where feature_name == raw_feat_name or feat_name
            actual_value = None
            for e in evidences:
                if getattr(e, 'feature_name', None) in (raw_feat_name, feat_name):
                    actual_value = getattr(e, 'original_value', None)
                    if actual_value is None:
                        actual_value = getattr(e, 'derived_value', None)
                    break
            
            top_drivers.append({
                "feature": feat_name,
                "value": actual_value,
                "shap_value": float(r.computation_value),
                "absolute_shap_value": abs(float(r.computation_value)),
                "direction": "increases anomaly" if float(r.computation_value) < 0 else "decreases anomaly",
                "meaning": meta["meaning"],
                "evidence_tier": meta["evidence_tier"]
            })
            
        # 2. Summary Generation
        driver_names = [d["feature"] for d in top_drivers]
        summary = f"This transaction is structurally unusual relative to the model reference population. "
        if len(driver_names) > 0:
            if len(driver_names) == 1:
                summary += f"The strongest model contributor was {driver_names[0]}."
            elif len(driver_names) == 2:
                summary += f"The strongest model contributors were {driver_names[0]} and {driver_names[1]}."
            else:
                summary += f"The strongest model contributors were {driver_names[0]}, {driver_names[1]}, and {driver_names[2]}."

        # 3. Investigation Caveats
        caveats = [
            "Anomaly indicates structural rarity, not criminality.",
            "Network observation does not establish IP ownership."
        ]
        
        # Check GeoIP missing
        # If there is no ENRICHED evidence for GeoIP, we can assume it's pending.
        if hasattr(alert, "dampeners_applied") and "UNRESOLVED_GEOIP" in getattr(alert, "dampeners_applied", []):
            caveats.append("GeoIP enrichment is unavailable in this run.")
            
        # Check Fee missing
        if hasattr(alert, "dampeners_applied") and "UNKNOWN_CANONICAL_FEE" in getattr(alert, "dampeners_applied", []):
            caveats.append("Canonical fee information was unavailable for this transaction.")
            
        # Check CIH heuristics
        has_cih = any(getattr(e, 'provenance_type', '') == 'HEURISTIC' and 'cih' in getattr(e, 'evidence_category', '').lower() for e in evidences)
        if has_cih:
            caveats.append("Common-input heuristics represent hypotheses rather than confirmed common control.")
            
        # Collaborative Dampener
        if hasattr(alert, "dampeners_applied") and "COLLABORATIVE_HEURISTIC_RISK" in getattr(alert, "dampeners_applied", []):
            caveats.append("The input structure spans multiple inferred common-input clusters and may reflect collaborative transaction construction, batching, or CoinJoin-like behavior.")
            
        # Add UTXO caveat (standard)
        caveats.append("Exact UTXO lineage cannot be established without prev_txid/prev_vout fields.")
        
        # Deduplicate caveats while preserving order
        unique_caveats = []
        for c in caveats:
            if c not in unique_caveats:
                unique_caveats.append(c)

        # 4. Provenance Tracing
        prov_refs = []
        for e in evidences:
            sf = getattr(e, 'source_file', None)
            sr = getattr(e, 'source_row', None)
            if sf and sr:
                prov_refs.append(f"{sf}:{sr}")
        unique_prov = list(set(prov_refs))
        
        # Format human-readable lead
        lead_lines = [
            "STRUCTURAL ANOMALY",
            "",
            "Transaction:",
            f"    {alert.txid}",
            "",
            "Anomaly Strength:",
            f"    {alert.anomaly_strength}",
            "",
            "Why it was surfaced:"
        ]
        
        for idx, d in enumerate(top_drivers, 1):
            lead_lines.append(f"    {idx}. {d['feature']} (value: {d['value']}, SHAP: {d['shap_value']:.4f})")
            lead_lines.append(f"       Meaning: {d['meaning']} [{d['evidence_tier']}]")
            lead_lines.append("")
            
        lead_lines.append("Supporting evidence:")
        lead_lines.append(f"    {len(evidences)} distinct evidence artifacts available.")
        lead_lines.append("")
        lead_lines.append("Investigation caveats:")
        for c in unique_caveats:
            lead_lines.append(f"    - {c}")
        lead_lines.append("")
        lead_lines.append("Evidence provenance:")
        if unique_prov:
            for p in unique_prov[:3]:
                lead_lines.append(f"    - {p}")
            if len(unique_prov) > 3:
                lead_lines.append(f"    - ... and {len(unique_prov)-3} more.")
        else:
            lead_lines.append("    Model derived.")
            
        lead_text = "\n".join(lead_lines)

        return {
            "alert_id": alert.alert_id,
            "txid": alert.txid,
            "anomaly_strength": alert.anomaly_strength,
            "summary": summary,
            "key_drivers": top_drivers,
            "supporting_evidence_count": len(evidences),
            "investigation_caveats": unique_caveats,
            "provenance": unique_prov,
            "human_readable_lead": lead_text
        }
