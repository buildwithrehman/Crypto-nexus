import unittest
import duckdb
from datetime import datetime
from decimal import Decimal

from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.schema import (
    NetworkObservation, 
    Transaction, 
    QuarantineRecord, 
    ProvenanceMetadata,
    IngestionMetadata
)

class TestDuckDBPersistence(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_schema_initialization(self):
        # Verify that all 8 tables were created
        tables = self.conn.execute("SHOW TABLES").fetchall()
        table_names = {t[0] for t in tables}
        expected_tables = {
            'pipeline_runs', 'run_uploads', 'ingestion_runs', 'raw_records', 'transactions', 'network_obs', 
            'addresses', 'tx_inputs', 'tx_outputs', 'quarantine_errors', 'ip_enrichment', 
            'entity_clusters', 'cluster_members', 'clustering_evidence',
            'alerts', 'alert_reasons', 'alert_evidence'
        }
        self.assertEqual(expected_tables, table_names)

    def test_insert_ingestion_run(self):
        meta = IngestionMetadata(
            run_id="run_123",
            source_file="data.csv",
            ingestion_timestamp=datetime(2023, 1, 1, 12, 0, 0),
            record_count=100,
            quarantine_count=5
        )
        self.repo.insert_ingestion_run(meta)
        
        # Verify insertion
        result = self.conn.execute("SELECT run_id, record_count FROM ingestion_runs WHERE run_id='run_123'").fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "run_123")
        self.assertEqual(result[1], 100)

    def test_insert_quarantine_record(self):
        record = QuarantineRecord(
            run_id="run_123",
            source_file="data.csv",
            source_row=42,
            raw_data={"txid": "deadbeef", "bad_field": True},
            rejection_reason="Duplicate txid",
            quarantine_timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        self.repo.insert_quarantine_record(record)
        
        # Verify insertion and JSON handling
        result = self.conn.execute("SELECT source_row, raw_data, rejection_reason FROM quarantine_errors WHERE run_id='run_123'").fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 42)
        # DuckDB returns JSON as a string
        self.assertIn("deadbeef", result[1])
        self.assertEqual(result[2], "Duplicate txid")

    def test_insert_accepted_record(self):
        # 1. Setup ingestion run first (for FK constraints if enforced)
        self.conn.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run_123', 'data.csv', current_timestamp)")

        obs = NetworkObservation(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=8333,
            txid="tx_001"
        )
        tx = Transaction(
            txid="tx_001",
            input_addresses=["addr1"],
            output_addresses=["addr2"],
            input_amounts=[Decimal("1.5")],
            output_amounts=[Decimal("1.4")],
            fee=Decimal("0.1"),
            script_type="p2pkh"
        )
        prov = ProvenanceMetadata(
            run_id="run_123",
            source_file="data.csv",
            source_row=1,
            extracted_timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )

        # 2. Test insertion
        self.repo.insert_accepted_record(obs, tx, prov)

        # 3. Verify provenance
        raw = self.conn.execute("SELECT run_id, source_file, source_row FROM raw_records WHERE source_row=1").fetchone()
        self.assertEqual(raw, ("run_123", "data.csv", 1))

        # 4. Verify transaction
        tx_row = self.conn.execute("SELECT txid, fee, script_type FROM transactions WHERE txid='tx_001'").fetchone()
        self.assertEqual(tx_row[0], "tx_001")
        self.assertEqual(float(tx_row[1]), 0.1)

        # 5. Verify network observation
        obs_row = self.conn.execute("SELECT src_ip, dst_ip, txid FROM network_obs WHERE txid='tx_001'").fetchone()
        self.assertEqual(obs_row, ("192.168.1.1", "10.0.0.1", "tx_001"))

        # 6. Verify addresses and inputs/outputs
        addrs = {r[0] for r in self.conn.execute("SELECT address FROM addresses").fetchall()}
        self.assertEqual(addrs, {"addr1", "addr2"})

        inputs = self.conn.execute("SELECT amount FROM tx_inputs WHERE txid='tx_001'").fetchone()
        self.assertEqual(float(inputs[0]), 1.5)

    def test_atomicity_rollback(self):
        self.conn.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run_rollback', 'data.csv', current_timestamp)")
        
        obs = NetworkObservation(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=8333,
            txid="tx_rollback"
        )
        tx = Transaction(
            txid="tx_rollback",
            input_addresses=["addr_rollback"],
            output_addresses=["addr_rollback"],
            input_amounts=[Decimal("1.5")],
            output_amounts=[Decimal("1.4")],
            fee=Decimal("0.1"),
            script_type="p2pkh"
        )
        prov = ProvenanceMetadata(
            run_id="run_rollback",
            source_file="data.csv",
            source_row=99,
            extracted_timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # We will manually cause an exception by altering tx.txid midway, breaking FK constraints or something
        # Use a wrapper class to intercept and fail the query
        class BuggyConnection:
            def __init__(self, conn):
                self.conn = conn
            def execute(self, query, params=None):
                if "INSERT INTO tx_outputs" in query:
                    raise Exception("Simulated crash")
                if params:
                    return self.conn.execute(query, params)
                return self.conn.execute(query)
                
        self.repo.conn = BuggyConnection(self.conn)
        
        with self.assertRaises(Exception):
            self.repo.insert_accepted_record(obs, tx, prov)
            
        self.repo.conn = self.conn
        
        # Verify rollback - no raw_records, no transactions, etc.
        self.assertEqual(self.conn.execute("SELECT count(*) FROM raw_records WHERE source_row=99").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM transactions WHERE txid='tx_rollback'").fetchone()[0], 0)
        
    def test_foreign_key_integrity(self):
        # Insert a network_obs that references a non-existent transaction
        # Should raise duckdb.ConstraintException
        with self.assertRaises(duckdb.ConstraintException):
            self.conn.execute("""
                INSERT INTO network_obs (run_id, source_file, source_row, timestamp, src_ip, dst_ip, src_port, dst_port, txid)
                VALUES ('run_fk', 'fk.csv', 1, current_timestamp, '1.1.1.1', '2.2.2.2', 80, 443, 'NON_EXISTENT_TXID')
            """)


    def test_save_alerts(self):
        from backend.schema import Alert, AlertReason, AlertEvidence
        # Insert raw requirements first
        self.repo.conn.execute("INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp) VALUES ('r1', 'f', 1, current_timestamp)")
        self.repo.conn.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx1', 'r1', 'f', 1)")
        
        a = Alert(
            alert_id="a1",
            run_id="run_1",
            txid="tx1",
            anomaly_strength=99.0,
            evidential_strength_tier="OBSERVED",
            operational_queue_rank=1,
            model_version="v1",
            dampeners_applied=["UNKNOWN_CANONICAL_FEE"]
        )
        r = AlertReason(
            alert_id="a1", reason_text="text", signal_type="ML_DERIVED",
            feature_name="f", computation_value=0.5
        )
        e = AlertEvidence(
            evidence_id="e1", alert_id="a1", evidence_category="OBSERVED",
            provenance_type="DIRECT", source_file="f", source_row=1,
            uncertainty_semantics="None"
        )
        
        self.repo.save_alerts([a], [r], [e])
        
        saved_alerts = self.repo.conn.execute("SELECT * FROM alerts").fetchall()
        self.assertEqual(len(saved_alerts), 1)
        self.assertEqual(saved_alerts[0][0], "a1")
        
        saved_reasons = self.repo.conn.execute("SELECT * FROM alert_reasons").fetchall()
        self.assertEqual(len(saved_reasons), 1)
        
        saved_evs = self.repo.conn.execute("SELECT * FROM alert_evidence").fetchall()
        self.assertEqual(len(saved_evs), 1)

if __name__ == '__main__':
    unittest.main()
