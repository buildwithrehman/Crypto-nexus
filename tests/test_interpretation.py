import unittest
from backend.scoring.interpretation import EvidenceInterpreter, FEATURE_METADATA
from backend.schema import Alert, AlertReason, AlertEvidence

class MockAlert:
    def __init__(self, txid, alert_id, anomaly_strength, dampeners_applied=None):
        self.txid = txid
        self.alert_id = alert_id
        self.anomaly_strength = anomaly_strength
        self.dampeners_applied = dampeners_applied or []

class MockReason:
    def __init__(self, feature_name, computation_value):
        self.feature_name = feature_name
        self.computation_value = computation_value

class MockEvidence:
    def __init__(self, feature_name, category, source_file=None, source_row=None, val=None, prov="DERIVED"):
        self.feature_name = feature_name
        self.evidence_category = category
        self.source_file = source_file
        self.source_row = source_row
        self.original_value = val
        self.derived_value = val
        self.provenance_type = prov

class TestEvidenceInterpreter(unittest.TestCase):
    def test_feature_metadata_completeness(self):
        canonical_features = [
            "in_degree", "out_degree", "total_degree", "betweenness", 
            "louvain_community", "is_peel_chain", "weighted_in_degree", 
            "weighted_out_degree", "weighted_total_degree", "fee", 
            "average_input_value", "average_output_value", "unique_in_addresses", 
            "unique_out_addresses", "unique_ip_propagators", "propagation_edge_count", 
            "duration_active_seconds"
        ]
        for f in canonical_features:
            self.assertIn(f, FEATURE_METADATA, f"Missing {f}")
        self.assertEqual(len(FEATURE_METADATA), 17)

    def test_deterministic_explanation(self):
        alert = MockAlert("tx123", "a1", 99.9)
        reasons = [
            MockReason("unique_ip_propagators", 2.5),
            MockReason("duration_active_seconds", -3.1),
            MockReason("propagation_edge_count", 1.2),
            MockReason("fee", 0.1) # 4th, should be ignored for top 3
        ]
        evidences = [
            MockEvidence("unique_ip_propagators", "FEATURE_CALCULATION", "obs.csv", 10, 7),
            MockEvidence("duration_active_seconds", "FEATURE_CALCULATION", "obs.csv", 10, 100),
            MockEvidence(None, "NETWORK_ENRICHMENT", None, None) # GeoIP present
        ]
        
        tx_details = {"fee": 1000}
        
        explanation = EvidenceInterpreter.generate_explanation(alert, reasons, evidences, tx_details)
        
        self.assertEqual(len(explanation["key_drivers"]), 3)
        self.assertEqual(explanation["key_drivers"][0]["feature"], "duration_active_seconds")
        self.assertEqual(explanation["key_drivers"][0]["direction"], "increases anomaly")
        
        self.assertEqual(explanation["key_drivers"][1]["feature"], "unique_ip_propagators")
        self.assertEqual(explanation["key_drivers"][1]["value"], 7)
        self.assertEqual(explanation["key_drivers"][1]["evidence_tier"], "DERIVED")
        
        # Check provenance
        self.assertIn("obs.csv:10", explanation["provenance"])
        
        # Missing CIH/Collaborative Dampener means they shouldn't be in caveats
        caveat_str = " ".join(explanation["investigation_caveats"])
        self.assertNotIn("GeoIP enrichment is unavailable", caveat_str)
        self.assertNotIn("fee information was unavailable", caveat_str)
        self.assertNotIn("CoinJoin", caveat_str)

    def test_caveats(self):
        alert = MockAlert("tx123", "a1", 99.9, ["COLLABORATIVE_HEURISTIC_RISK", "UNRESOLVED_GEOIP", "UNKNOWN_CANONICAL_FEE"])
        reasons = []
        evidences = [
            MockEvidence(None, "HEURISTIC_EVIDENCE", "tx.csv", 5, prov="HEURISTIC")
        ]
        
        explanation = EvidenceInterpreter.generate_explanation(alert, reasons, evidences, None)
        caveat_str = " ".join(explanation["investigation_caveats"])
        
        self.assertIn("GeoIP enrichment is unavailable", caveat_str)
        self.assertIn("fee information was unavailable", caveat_str)
        self.assertIn("CoinJoin", caveat_str)
        # It's not CIH, so CIH caveat shouldn't be there, unless category has 'cih'
        self.assertNotIn("hypotheses rather than confirmed common control", caveat_str)
        
    def test_cih_caveat(self):
        alert = MockAlert("tx123", "a1", 99.9)
        evidences = [
            MockEvidence(None, "cih_heuristic", prov="HEURISTIC")
        ]
        explanation = EvidenceInterpreter.generate_explanation(alert, [], evidences, None)
        caveat_str = " ".join(explanation["investigation_caveats"])
        self.assertIn("hypotheses rather than confirmed common control", caveat_str)

    def test_wording_safety(self):
        # We must NOT use "belongs to sender", etc.
        for meta in FEATURE_METADATA.values():
            m = meta["meaning"].lower()
            self.assertNotIn("belongs to", m)
            self.assertNotIn("wallet owner", m)
            self.assertNotIn("originated from", m)

if __name__ == '__main__':
    unittest.main()
