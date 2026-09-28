import unittest
from backend.ingestion.validator import DataValidator
from backend.schema import NetworkObservation, Transaction, QuarantineRecord, ProvenanceMetadata

class TestDataValidator(unittest.TestCase):
    def setUp(self):
        self.validator = DataValidator(run_id="test_run_1", source_file="test.csv")
        self.valid_record = {
            "timestamp": "2023-01-01T12:00:00",
            "src_ip": "192.168.1.1",
            "dst_ip": "10.0.0.1",
            "src_port": 12345,
            "dst_port": 8333,
            "txid": "deadbeef",
            "input_addresses": ["addr1", "addr2"],
            "output_addresses": ["addr3"],
            "input_amounts": [1.5, 2.0],
            "output_amounts": [3.4],
            "fee": 0.1,
            "script_type": "p2pkh"
        }

    def test_valid_record(self):
        is_valid, result = self.validator.validate_record(self.valid_record, 1)
        self.assertTrue(is_valid)
        obs, tx, prov = result
        self.assertIsInstance(obs, NetworkObservation)
        self.assertIsInstance(tx, Transaction)
        self.assertIsInstance(prov, ProvenanceMetadata)
        self.assertEqual(tx.txid, "deadbeef")

    def test_duplicate_txid(self):
        is_valid, result = self.validator.validate_record(self.valid_record, 1)
        self.assertTrue(is_valid)
        
        # Validate same record again (same txid)
        is_valid2, result2 = self.validator.validate_record(self.valid_record, 2)
        self.assertFalse(is_valid2)
        self.assertIsInstance(result2, QuarantineRecord)
        self.assertIn("Duplicate txid", result2.rejection_reason)

    def test_invalid_ip(self):
        bad_record = self.valid_record.copy()
        bad_record["src_ip"] = "999.999.999.999" # invalid IP
        bad_record["txid"] = "tx2"
        is_valid, result = self.validator.validate_record(bad_record, 2)
        self.assertFalse(is_valid)
        self.assertIsInstance(result, QuarantineRecord)
        self.assertIn("Invalid IP address format", result.rejection_reason)

    def test_invalid_port(self):
        bad_record = self.valid_record.copy()
        bad_record["dst_port"] = 70000 # out of range
        bad_record["txid"] = "tx3"
        is_valid, result = self.validator.validate_record(bad_record, 3)
        self.assertFalse(is_valid)
        self.assertIn("out of range", result.rejection_reason)
        
        bad_record["dst_port"] = "notaport"
        bad_record["txid"] = "tx4"
        is_valid, result = self.validator.validate_record(bad_record, 4)
        self.assertFalse(is_valid)
        self.assertIn("Invalid port format", result.rejection_reason)

    def test_negative_monetary_value(self):
        bad_record = self.valid_record.copy()
        bad_record["input_amounts"] = [1.5, -2.0]
        bad_record["txid"] = "tx5"
        is_valid, result = self.validator.validate_record(bad_record, 5)
        self.assertFalse(is_valid)
        self.assertIn("Negative monetary value detected", result.rejection_reason)

    def test_array_alignment(self):
        bad_record = self.valid_record.copy()
        bad_record["input_amounts"] = [1.5] # mismatch length
        del bad_record["fee"] # Remove fee so we don't trigger fee validation before array alignment
        bad_record["txid"] = "tx6"
        is_valid, result = self.validator.validate_record(bad_record, 6)
        self.assertFalse(is_valid)
        self.assertIn("Array length mismatch", result.rejection_reason)

    def test_missing_required_field(self):
        bad_record = self.valid_record.copy()
        del bad_record["timestamp"]
        bad_record["txid"] = "tx7"
        is_valid, result = self.validator.validate_record(bad_record, 7)
        self.assertFalse(is_valid)
        self.assertIn("timestamp", result.rejection_reason.lower())

    def test_unexpected_internal_exception(self):
        from unittest.mock import patch
        with patch('backend.ingestion.validator.NetworkObservation') as mock_model:
            # Force a generic Exception (like an internal logic bug)
            mock_model.side_effect = TypeError("Internal software bug simulated")
            with self.assertRaises(TypeError):
                self.validator.validate_record(self.valid_record, 8)

if __name__ == '__main__':
    unittest.main()
