import unittest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from backend.schema import (
    NetworkObservation,
    Transaction,
    Address,
    IPEnrichment,
    IngestionMetadata,
    QuarantineRecord,
    ProvenanceMetadata
)

class TestCanonicalDataContract(unittest.TestCase):

    def test_valid_network_observation(self):
        obs = NetworkObservation(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=8333,
            txid="deadbeef"
        )
        self.assertEqual(obs.src_ip, "192.168.1.1")
        self.assertEqual(obs.dst_port, 8333)

    def test_valid_transaction(self):
        tx = Transaction(
            txid="deadbeef",
            input_addresses=["addr1", "addr2"],
            output_addresses=["addr3"],
            input_amounts=[Decimal("1.5"), Decimal("2.0")],
            output_amounts=[Decimal("3.4")],
            fee=Decimal("0.1"),
            script_type="p2pkh"
        )
        self.assertEqual(tx.txid, "deadbeef")
        self.assertEqual(len(tx.input_addresses), 2)
        self.assertEqual(tx.fee, Decimal("0.1"))

    def test_valid_address(self):
        addr = Address(address="addr1")
        self.assertEqual(addr.address, "addr1")

    def test_valid_enrichment(self):
        enrichment = IPEnrichment(
            ip_address="8.8.8.8",
            geo_country="US",
            asn="AS15169"
        )
        self.assertEqual(enrichment.geo_country, "US")

    def test_missing_required_field(self):
        with self.assertRaises(ValidationError):
            NetworkObservation(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                # src_ip is missing
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=8333,
                txid="deadbeef"
            )

    def test_malformed_field(self):
        with self.assertRaises(ValidationError):
            NetworkObservation(
                timestamp="invalid_timestamp", # malformed
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=8333,
                txid="deadbeef"
            )

    def test_array_length_mismatch(self):
        with self.assertRaises(ValidationError) as context:
            Transaction(
                txid="deadbeef",
                input_addresses=["addr1"],
                output_addresses=["addr3"],
                input_amounts=[Decimal("1.5"), Decimal("2.0")], # mismatch! 1 address, 2 amounts
                output_amounts=[Decimal("3.4")]
            )
        self.assertIn("Array length mismatch", str(context.exception))

    def test_provenance_metadata_representation(self):
        prov = ProvenanceMetadata(
            run_id="run_001",
            source_file="traffic.csv",
            source_row=42,
            extracted_timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        self.assertEqual(prov.run_id, "run_001")
        self.assertEqual(prov.source_row, 42)

    def test_quarantine_metadata_representation(self):
        quar = QuarantineRecord(
            run_id="run_001",
            source_file="traffic.csv",
            source_row=42,
            raw_data={"src_ip": "invalid"},
            rejection_reason="Missing txid",
            quarantine_timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        self.assertEqual(quar.rejection_reason, "Missing txid")

    def test_serialization_deserialization(self):
        tx = Transaction(
            txid="deadbeef",
            input_addresses=["addr1"],
            output_addresses=["addr3"],
            input_amounts=[Decimal("1.5")],
            output_amounts=[Decimal("1.4")],
            fee=Decimal("0.1")
        )
        # Serialize to JSON string
        json_data = tx.model_dump_json()
        
        # Deserialize back to model
        tx_loaded = Transaction.model_validate_json(json_data)
        
        self.assertEqual(tx_loaded.txid, tx.txid)
        self.assertEqual(tx_loaded.input_amounts, tx.input_amounts)
        self.assertEqual(tx_loaded.fee, tx.fee)

if __name__ == '__main__':
    unittest.main()
