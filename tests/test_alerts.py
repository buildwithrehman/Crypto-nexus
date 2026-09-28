import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from backend.scoring.alerts import AlertEngine
from backend.schema import Alert, AlertReason, AlertEvidence

class TestAlerts(unittest.TestCase):
    def setUp(self):
        self.engine = AlertEngine(run_id="run1", model_version="v1")
        self.engine.reference_scores = np.array([0.1, 0.5, 0.5, 0.8, 0.9, 0.95])
        
        self.ml_results = pd.DataFrame({
            "tx_id": ["tx1"],
            "is_anomaly": [1],
            "anomaly_score": [0.9],
            "shap_reasons": [[{"feature": "f1", "contribution": -0.1}]]
        })
        self.df_features = pd.DataFrame({"tx_id": ["tx1"]})
        self.tx_timestamps = {"tx1": datetime(2024, 1, 1, 10, 0)}
        self.evidence_records = {
            "tx1": [{
                "category": "OBSERVED", "provenance_type": "DIRECT", 
                "source_file": "net.csv", "source_row": 10
            }]
        }

    def test_empirical_cdf(self):
        # Reference population: [0.1, 0.5, 0.5, 0.8, 0.9, 0.95]
        # Length N = 6
        engine = AlertEngine(run_id="run2", model_version="v1")
        engine.reference_scores = np.array([0.1, 0.5, 0.5, 0.8, 0.9, 0.95])
        
        test_scores = [
            -0.5, # Below min -> 0 <= ref -> 0/6 = 0%
            0.1,  # Equal to min -> 1/6 = 16.66%
            0.5,  # Multiple identical reference -> count <= 0.5 is 3 -> 3/6 = 50%
            0.5,  # Identical score -> exactly same percentile -> 50%
            0.8,  # Equal to existing -> 4/6 = 66.66%
            0.85, # Between ref values -> 4/6 = 66.66%
            0.95, # Equal to max -> 6/6 = 100%
            1.5   # Above max -> 6/6 = 100%
        ]
        
        ml_results = pd.DataFrame({
            "tx_id": [f"tx_{i}" for i in range(len(test_scores))],
            "is_anomaly": [1]*len(test_scores),
            "anomaly_score": test_scores,
            "shap_reasons": [[]]*len(test_scores)
        })
        df_features = pd.DataFrame({"tx_id": ml_results["tx_id"]})
        tx_ts = {tx: datetime(2024,1,1) for tx in ml_results["tx_id"]}
        ev = {tx: [{"category": "OBSERVED", "provenance_type": "DIRECT", "source_file": "f", "source_row": 1}] for tx in ml_results["tx_id"]}
        
        alerts, _, _ = engine.generate_alerts(ml_results, df_features, tx_ts, ev)
        
        pcts = {a.txid: a.anomaly_strength for a in alerts}
        
        self.assertAlmostEqual(pcts["tx_0"], 0.0)
        self.assertAlmostEqual(pcts["tx_1"], 16.666666666666664)
        self.assertAlmostEqual(pcts["tx_2"], 50.0) # Identical reference ties
        self.assertEqual(pcts["tx_2"], pcts["tx_3"]) # Identical scores -> identical percentile
        self.assertAlmostEqual(pcts["tx_4"], 66.66666666666666)
        self.assertAlmostEqual(pcts["tx_5"], 66.66666666666666)
        self.assertAlmostEqual(pcts["tx_6"], 100.0) # Max -> 100
        self.assertAlmostEqual(pcts["tx_7"], 100.0) # Above max -> 100
        
        # Monotonicity check: results are sorted by anomaly_strength DESC
        scores = list(pcts.values())
        self.assertTrue(all(scores[i] >= scores[i+1] for i in range(len(scores)-1)))

    def test_collaborative_cih_dampener(self):
        engine = self.engine
        
        # 1. All inputs belong to one CIH cluster -> no dampener
        tx_input_clusters = {"tx1": {101}}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertNotIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)
        
        # 2. Inputs belong to two distinct CIH clusters -> dampener
        tx_input_clusters = {"tx1": {101, 102}}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

        # 3. Inputs belong to three clusters -> dampener
        tx_input_clusters = {"tx1": {101, 102, 103}}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

        # 4. Duplicate evidence for one cluster -> no false dampener (set inherently handles duplicates, but let's test input as a set with 1 item derived from duplicate rows)
        # Even if multiple addresses map to 101, it's one distinct cluster.
        tx_input_clusters = {"tx1": {101}}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertNotIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

        # 5. Output-address clusters alone -> no dampener
        # Since we explicitly only pass `tx_input_clusters` to generate_alerts (representing the inputs), outputs don't even enter the parameter.
        tx_input_clusters = {}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertNotIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

        # 6. Missing cluster membership -> no invented cluster
        tx_input_clusters = {"tx1": set()}
        alerts, _, _ = engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records, tx_input_clusters)
        self.assertNotIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

    def test_evidence_id_determinism(self):
        # 1. same evidence -> same ID
        id1 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 10, None, None, None, ["ref1", "ref2"], None, None)
        id1_dup = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 10, None, None, None, ["ref1", "ref2"], None, None)
        self.assertEqual(id1, id1_dup)
        
        # 2. different source_file -> diff ID
        id2 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f2.csv", 10, None, None, None, ["ref1", "ref2"], None, None)
        self.assertNotEqual(id1, id2)
        
        # 3. different source_row -> diff ID
        id3 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 11, None, None, None, ["ref1", "ref2"], None, None)
        self.assertNotEqual(id1, id3)
        
        # 4. different underlying reference -> diff ID
        id4 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 10, None, None, None, ["ref1", "ref3"], None, None)
        self.assertNotEqual(id1, id4)
        
        # 5. different feature -> diff ID
        id5 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 10, None, None, "feature_X", ["ref1", "ref2"], None, None)
        self.assertNotEqual(id1, id5)
        
        # 6. Reordering non-semantic reference lists does not unexpectedly change identity
        # In _hash_evidence, lists of underlying references are sorted before hashing.
        id6 = self.engine._hash_evidence("a1", "OBSERVED", "DIRECT", "f1.csv", 10, None, None, None, ["ref2", "ref1"], None, None)
        self.assertEqual(id1, id6)

    def test_provenance_validation(self):
        # DIRECT missing file
        ev_bad1 = {"tx1": [{"category": "OBSERVED", "provenance_type": "DIRECT", "source_row": 10}]}
        with self.assertRaisesRegex(ValueError, "DIRECT provenance requires source_file and source_row"):
            self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, ev_bad1)
            
        # DERIVED_FROM with source_row
        ev_bad2 = {"tx1": [{"category": "DERIVED", "provenance_type": "DERIVED_FROM", "source_row": 10}]}
        with self.assertRaisesRegex(ValueError, "DERIVED_FROM must not contain source_file/source_row"):
            self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, ev_bad2)
            
        # MODEL_DERIVED_FROM without model_version
        ev_bad3 = {"tx1": [{"category": "ML_DERIVED", "provenance_type": "MODEL_DERIVED_FROM"}]}
        with self.assertRaisesRegex(ValueError, "MODEL_DERIVED_FROM provenance requires model_version"):
            self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, ev_bad3)
            
        # MODEL_DERIVED_FROM with source_row
        ev_bad4 = {"tx1": [{"category": "ML_DERIVED", "provenance_type": "MODEL_DERIVED_FROM", "model_version": "v1", "source_row": 1}]}
        with self.assertRaisesRegex(ValueError, "MODEL_DERIVED_FROM must not contain source_row"):
            self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, ev_bad4)

    def test_evidence_tier_invariant(self):
        # Alert tier equals highest tier actually present
        # Let's provide OBSERVED and HEURISTIC
        ev = {"tx1": [
            {"category": "HEURISTIC", "provenance_type": "DERIVED_FROM"},
            {"category": "OBSERVED", "provenance_type": "DIRECT", "source_file": "f", "source_row": 1}
        ]}
        alerts, _, _ = self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, ev)
        self.assertEqual(alerts[0].evidential_strength_tier, "OBSERVED")
        
        # Test failing closed if no evidence exists
        ml_results_no_shap = self.ml_results.copy()
        ml_results_no_shap.at[0, "shap_reasons"] = []
        with self.assertRaisesRegex(ValueError, "has no evidence attached. Failing closed."):
            self.engine.generate_alerts(ml_results_no_shap, self.df_features, self.tx_timestamps, {})
        
    def test_model_derived_chain(self):
        alerts, reasons, evidences = self.engine.generate_alerts(self.ml_results, self.df_features, self.tx_timestamps, self.evidence_records)
        shap_ev = next(e for e in evidences if e.provenance_type == "MODEL_DERIVED_FROM")
        self.assertEqual(shap_ev.underlying_evidence_references, [f"run_id:{self.engine.run_id}"])

    def test_queue_tie_breaking(self):
        engine = AlertEngine(run_id="run_queue", model_version="v1")
        engine.reference_scores = np.array([0.1, 0.5, 0.8])
        
        # 4 identical scores (so identical anomaly strength)
        ml_results = pd.DataFrame({
            "tx_id": ["tx1", "tx2", "tx3", "tx4"],
            "is_anomaly": [1, 1, 1, 1],
            "anomaly_score": [0.5, 0.5, 0.5, 0.5],
            "shap_reasons": [[], [], [], []]
        })
        df_features = pd.DataFrame({"tx_id": ["tx1", "tx2", "tx3", "tx4"]})
        
        # tx1 and tx2 have same tier, but tx2 has earlier timestamp
        tx_timestamps = {
            "tx1": datetime(2024, 1, 1, 12, 0),
            "tx2": datetime(2024, 1, 1, 10, 0), # older -> comes later in queue (DESC means newer first)
            "tx3": datetime(2024, 1, 1, 13, 0),
            "tx4": datetime(2024, 1, 1, 13, 0)
        }
        
        ev = {
            "tx1": [{"category": "HEURISTIC", "provenance_type": "DERIVED_FROM"}],
            "tx2": [{"category": "HEURISTIC", "provenance_type": "DERIVED_FROM"}],
            "tx3": [{"category": "OBSERVED", "provenance_type": "DIRECT", "source_file": "f", "source_row": 1}],
            "tx4": [{"category": "OBSERVED", "provenance_type": "DIRECT", "source_file": "f", "source_row": 1}]
        }
        
        alerts, _, _ = engine.generate_alerts(ml_results, df_features, tx_timestamps, ev)
        
        # Order should be:
        # 1. Anomaly strength (all tie at 50%)
        # 2. Tier (OBSERVED > HEURISTIC) => tx3, tx4 beat tx1, tx2
        # 3. Timestamp (DESC) => tx3 (13:00) vs tx4 (13:00) tie. tx1 (12:00) beats tx2 (10:00).
        # 4. txid (ASC) => tx3 beats tx4
        # Expected order: tx3, tx4, tx1, tx2
        
        self.assertEqual(alerts[0].txid, "tx3")
        self.assertEqual(alerts[1].txid, "tx4")
        self.assertEqual(alerts[2].txid, "tx1")
        self.assertEqual(alerts[3].txid, "tx2")

if __name__ == '__main__':
    unittest.main()
