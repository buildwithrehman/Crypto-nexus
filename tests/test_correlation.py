import unittest
from datetime import datetime
from decimal import Decimal
import duckdb

from backend.ingestion.validator import DataValidator
from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.correlation.service import CorrelationService
from backend.schema import NetworkObservation, Transaction, ProvenanceMetadata



class TestCorrelationService(unittest.TestCase):
    def setUp(self):
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)
        self.service = CorrelationService(self.conn)

        # Setup base metadata
        self.conn.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run_corr', 'data.csv', current_timestamp)")
        
        # Insert a transaction
        prov = ProvenanceMetadata(run_id="run_corr", source_file="data.csv", source_row=1, extracted_timestamp=datetime.utcnow())
        tx = Transaction(
            txid="tx_corr",
            input_addresses=["addr_in"],
            output_addresses=["addr_out"],
            input_amounts=[Decimal("1.12345678")],
            output_amounts=[Decimal("1.0")],
            fee=Decimal("0.12345678"),
            script_type="p2pkh"
        )
        obs1 = NetworkObservation(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            src_ip="192.168.1.1", dst_ip="10.0.0.1", src_port=1234, dst_port=8333, txid="tx_corr"
        )
        self.repo.insert_accepted_record(obs1, tx, prov)
        
        # Multiple observations for same TXID
        # ON CONFLICT DO NOTHING will ignore the duplicate txid insert but will insert the new network_obs.
        # But wait, insert_accepted_record groups them all.
        prov2 = ProvenanceMetadata(run_id="run_corr", source_file="data.csv", source_row=2, extracted_timestamp=datetime.utcnow())
        obs2 = NetworkObservation(
            timestamp=datetime(2023, 1, 1, 12, 5, 0),
            src_ip="192.168.1.2", dst_ip="10.0.0.1", src_port=5678, dst_port=8333, txid="tx_corr"
        )
        self.repo.insert_accepted_record(obs2, tx, prov2)

    def tearDown(self):
        self.conn.close()

    def test_ip_to_tx_correlation(self):
        res = self.service.get_ip_to_tx_correlation("192.168.1.1")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["txid"], "tx_corr")
        
        # Test unknown IP
        self.assertEqual(len(self.service.get_ip_to_tx_correlation("9.9.9.9")), 0)

    def test_multiple_observations_for_one_txid(self):
        res = self.service.get_tx_propagations("tx_corr")
        self.assertEqual(len(res), 2)
        ips = {r["src_ip"] for r in res}
        self.assertEqual(ips, {"192.168.1.1", "192.168.1.2"})

    def test_address_to_tx_relationships(self):
        inputs = self.service.get_address_inputs("addr_in")
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0]["txid"], "tx_corr")
        self.assertEqual(inputs[0]["amount"], Decimal("1.12345678"))
        
        outputs = self.service.get_address_outputs("addr_out")
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0]["txid"], "tx_corr")
        self.assertEqual(outputs[0]["amount"], Decimal("1.0"))
        
        # Unknown address
        self.assertEqual(len(self.service.get_address_inputs("addr_unknown")), 0)

    def test_temporal_relationship(self):
        timeline = self.service.get_tx_timeline("tx_corr")
        self.assertEqual(timeline["txid"], "tx_corr")
        self.assertEqual(timeline["observation_count"], 2)
        self.assertEqual(timeline["first_observed"], datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(timeline["last_observed"], datetime(2023, 1, 1, 12, 5, 0))
        
        # Timeline for unknown TXID
        self.assertEqual(self.service.get_tx_timeline("tx_unknown"), {})

    def test_provenance_traceability(self):
        res = self.service.get_ip_to_tx_correlation("192.168.1.1")
        self.assertEqual(res[0]["run_id"], "run_corr")
        self.assertEqual(res[0]["source_file"], "data.csv")
        self.assertEqual(res[0]["source_row"], 1)

    def test_no_owns_relationship(self):
        # We explicitly verify that the service only returns 'propagations' or 'inputs/outputs'
        # The API surface prevents making statements like "Address owns IP"
        self.assertTrue(hasattr(self.service, "get_ip_to_tx_correlation"))
        self.assertTrue(hasattr(self.service, "get_address_inputs"))
        self.assertFalse(hasattr(self.service, "get_ip_owners"))

    def test_missing_utxo_lineage(self):
        # We verify that without prev_txid, the system only knows Address -> Transaction correlations,
        # but does not attempt to fabricate a previous transaction.
        res = self.service.get_address_inputs("addr_in")
        self.assertNotIn("prev_txid", res[0])

    def test_fee_validation(self):
        res = self.service.validate_transaction_fee("tx_corr")
        self.assertEqual(res["status"], "consistent")
        self.assertEqual(res["calculated_fee"], Decimal("0.12345678"))
        
        # Unknown TXID
        self.assertEqual(self.service.validate_transaction_fee("unknown")["status"], "unknown_txid")

if __name__ == '__main__':
    unittest.main()
