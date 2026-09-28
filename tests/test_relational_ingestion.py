import unittest
import duckdb
import os
import tempfile
import uuid
from datetime import datetime
from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.ingestion.loader import IngestionLoader
from backend.schema import IngestionMetadata

class TestRelationalIngestionBridge(unittest.TestCase):
    def setUp(self):
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)
        self.loader = IngestionLoader(self.repo)
        self.run_id = "test_run_" + uuid.uuid4().hex
        
        self.test_dir = tempfile.TemporaryDirectory()
        
        # Valid Transaction File (contains a duplicate TXID to test canonical constraint)
        self.tx_path = os.path.join(self.test_dir.name, "transactions.csv")
        with open(self.tx_path, "w") as f:
            f.write("txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n")
            f.write("tx1,addr1,addr2,1.0,0.9,0.1,p2pkh\n")
            f.write("tx1,addr3,addr4,2.0,1.9,0.1,p2pkh\n") # DUPLICATE! Should be quarantined
            f.write("tx2,addr5,addr6,3.0,2.9,0.1,p2pkh\n")
            
        # Valid Network Observations File (contains duplicate TXIDs to test relational constraint, plus unknown TXID)
        self.obs_path = os.path.join(self.test_dir.name, "observations.csv")
        with open(self.obs_path, "w") as f:
            f.write("txid,timestamp,src_ip,dst_ip,src_port,dst_port\n")
            f.write("tx1,2023-01-01T12:00:00Z,1.1.1.1,2.2.2.2,12345,8333\n")
            f.write("tx1,2023-01-01T12:00:05Z,3.3.3.3,4.4.4.4,23456,8333\n") # ALLOWED duplicate txid
            f.write("tx2,2023-01-01T12:01:00Z,5.5.5.5,6.6.6.6,34567,8333\n")
            f.write("tx_unknown,2023-01-01T12:02:00Z,7.7.7.7,8.8.8.8,45678,8333\n") # UNKNOWN txid

    def tearDown(self):
        self.test_dir.cleanup()
        self.conn.close()

    def test_relational_ingestion_semantics(self):
        # 1. Load transactions
        tx_meta = self.loader.load_transaction_file(self.run_id, self.tx_path)
        self.assertEqual(tx_meta.record_count, 2, "Should accept 2 unique canonical txs")
        self.assertEqual(tx_meta.quarantine_count, 1, "Should quarantine 1 duplicate tx")
        
        tx_count = self.conn.execute("SELECT COUNT(*) FROM transactions WHERE run_id = ?", [self.run_id]).fetchone()[0]
        self.assertEqual(tx_count, 2)
        
        # 2. Load observations
        obs_meta = self.loader.load_observation_file(self.run_id, self.obs_path)
        self.assertEqual(obs_meta.record_count, 3, "Should accept 3 observations (including multiple for tx1)")
        self.assertEqual(obs_meta.quarantine_count, 1, "Should quarantine 1 unknown txid")
        
        obs_count = self.conn.execute("SELECT COUNT(*) FROM network_obs WHERE run_id = ?", [self.run_id]).fetchone()[0]
        self.assertEqual(obs_count, 3)
        
        # Verify run isolation by loading into a new run
        run_id2 = "test_run_" + uuid.uuid4().hex
        self.loader.load_transaction_file(run_id2, self.tx_path)
        self.loader.load_observation_file(run_id2, self.obs_path)
        
        total_obs = self.conn.execute("SELECT COUNT(*) FROM network_obs").fetchone()[0]
        self.assertEqual(total_obs, 6, "Run isolation prevents cross-run bleeding")
        
        # Verify provenance
        prov_tx1 = self.conn.execute("SELECT source_file, source_row FROM raw_records WHERE run_id = ? AND source_row = 1 AND source_file LIKE '%transactions%'", [self.run_id]).fetchone()
        self.assertIsNotNone(prov_tx1)
        
        prov_obs1 = self.conn.execute("SELECT source_file, source_row FROM raw_records WHERE run_id = ? AND source_row = 1 AND source_file LIKE '%observations%'", [self.run_id]).fetchone()
        self.assertIsNotNone(prov_obs1)

if __name__ == '__main__':
    unittest.main()
