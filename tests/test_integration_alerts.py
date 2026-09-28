import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from backend.database.connection import get_connection, initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.scoring.alerts import AlertEngine
from backend.scoring.runner import fetch_tx_input_clusters

class TestAlertIntegration(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)
        
    def tearDown(self):
        self.conn.close()
        
    def test_fetch_tx_input_clusters_and_dampener(self):
        # Insert a transaction with inputs in distinct CIH clusters
        
        self.repo.conn.execute("INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp) VALUES ('r1', 'f', 1, current_timestamp)")
        self.repo.conn.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx_collab', 'r1', 'f', 1)")
        self.repo.conn.execute("INSERT INTO addresses (address) VALUES ('addr1')")
        self.repo.conn.execute("INSERT INTO addresses (address) VALUES ('addr2')")
        self.repo.conn.execute("INSERT INTO addresses (address) VALUES ('addr_out')")
        
        # Two inputs
        self.repo.conn.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx_collab', 0, 'addr1', 1.0)")
        self.repo.conn.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx_collab', 1, 'addr2', 1.0)")
        
        # One output
        self.repo.conn.execute("INSERT INTO tx_outputs (txid, output_index, address, amount) VALUES ('tx_collab', 0, 'addr_out', 2.0)")
        
        # Create Phase 8 clusters
        self.repo.conn.execute("INSERT INTO entity_clusters (cluster_id, run_id, creation_timestamp) VALUES (101, 'r1', current_timestamp)")
        self.repo.conn.execute("INSERT INTO entity_clusters (cluster_id, run_id, creation_timestamp) VALUES (102, 'r1', current_timestamp)")
        self.repo.conn.execute("INSERT INTO entity_clusters (cluster_id, run_id, creation_timestamp) VALUES (999, 'r1', current_timestamp)")
        
        # Input addresses in distinct clusters
        self.repo.conn.execute("INSERT INTO cluster_members (cluster_id, address) VALUES (101, 'addr1')")
        self.repo.conn.execute("INSERT INTO cluster_members (cluster_id, address) VALUES (102, 'addr2')")
        
        # Output address in some cluster (should not affect dampener)
        self.repo.conn.execute("INSERT INTO cluster_members (cluster_id, address) VALUES (999, 'addr_out')")
        
        # Cross-run/stale cluster membership for addr1 (simulate a previous run)
        self.repo.conn.execute("INSERT INTO entity_clusters (cluster_id, run_id, creation_timestamp) VALUES (103, 'r0_stale', current_timestamp)")
        self.repo.conn.execute("INSERT INTO cluster_members (cluster_id, address) VALUES (103, 'addr1')")
        
        # Fetch the wiring, explicitly scoping to run 'r1'
        tx_input_clusters = fetch_tx_input_clusters(self.repo, "r1", ["tx_collab"])
        
        # Verify wiring only sees inputs from run 'r1'
        self.assertIn("tx_collab", tx_input_clusters)
        self.assertEqual(tx_input_clusters["tx_collab"], {101, 102})
        self.assertNotIn(999, tx_input_clusters["tx_collab"]) # Output cluster is excluded
        self.assertNotIn(103, tx_input_clusters["tx_collab"]) # Stale cross-run cluster is excluded
        
        # Now run the AlertEngine
        engine = AlertEngine(run_id="r1", model_version="v1")
        engine.reference_scores = np.array([0.5, 0.9])
        
        ml_results = pd.DataFrame({
            "tx_id": ["tx_collab"],
            "is_anomaly": [1],
            "anomaly_score": [0.9],
            "shap_reasons": [[{"feature": "f1", "contribution": 0.5}]]
        })
        df_features = pd.DataFrame({"tx_id": ["tx_collab"]})
        tx_ts = {"tx_collab": datetime.now()}
        ev = {"tx_collab": []}
        
        alerts, reasons, evidences = engine.generate_alerts(
            ml_results, df_features, tx_ts, ev, tx_input_clusters=tx_input_clusters
        )
        
        # Verify COLLABORATIVE_HEURISTIC_RISK dampener is active
        self.assertEqual(len(alerts), 1)
        self.assertIn("COLLABORATIVE_HEURISTIC_RISK", alerts[0].dampeners_applied)

if __name__ == '__main__':
    unittest.main()
