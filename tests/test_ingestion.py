import unittest
import os
import tempfile
import duckdb
from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.ingestion.loader import IngestionLoader

class TestIngestionLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)
        self.loader = IngestionLoader(self.repo)
        
        # Valid CSV
        self.csv_path = os.path.join(self.test_dir.name, "valid.csv")
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n")
            f.write("2023-01-01T12:00:00,192.168.1.1,10.0.0.1,12345,8333,csv_tx,addr1;addr2,addr3,1.12345678;2.0,3.02345678,0.1,p2pkh\n")
            
        # JSON Array
        self.json_path = os.path.join(self.test_dir.name, "valid.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write('''[
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "src_ip": "192.168.1.1",
                    "dst_ip": "10.0.0.1",
                    "src_port": "12345",
                    "dst_port": "8333",
                    "txid": "json_tx",
                    "input_addresses": ["addr1", "addr2"],
                    "output_addresses": ["addr3"],
                    "input_amounts": ["1.12345678", "2.0"],
                    "output_amounts": ["3.02345678"],
                    "fee": "0.1",
                    "script_type": "p2pkh"
                }
            ]''')
            
        # JSONL
        self.jsonl_path = os.path.join(self.test_dir.name, "valid.jsonl")
        with open(self.jsonl_path, "w", encoding="utf-8") as f:
            f.write('''{"timestamp": "2023-01-01T12:00:00", "src_ip": "192.168.1.1", "dst_ip": "10.0.0.1", "src_port": "12345", "dst_port": "8333", "txid": "jsonl_tx", "input_addresses": ["addr1", "addr2"], "output_addresses": ["addr3"], "input_amounts": ["1.12345678", "2.0"], "output_amounts": ["3.02345678"], "fee": "0.1", "script_type": "p2pkh"}
            ''')
            
        # XML
        self.xml_path = os.path.join(self.test_dir.name, "valid.xml")
        with open(self.xml_path, "w", encoding="utf-8") as f:
            f.write('''<records>
                <record>
                    <timestamp>2023-01-01T12:00:00</timestamp>
                    <src_ip>192.168.1.1</src_ip>
                    <dst_ip>10.0.0.1</dst_ip>
                    <src_port>12345</src_port>
                    <dst_port>8333</dst_port>
                    <txid>xml_tx</txid>
                    <input_addresses><item>addr1</item><item>addr2</item></input_addresses>
                    <output_addresses><item>addr3</item></output_addresses>
                    <input_amounts><item>1.12345678</item><item>2.0</item></input_amounts>
                    <output_amounts><item>3.02345678</item></output_amounts>
                    <fee>0.1</fee>
                    <script_type>p2pkh</script_type>
                </record>
            </records>''')
            
        # Mixed CSV (Valid, Missing Required, Duplicate TXID, Malformed Monetary)
        self.mixed_path = os.path.join(self.test_dir.name, "mixed.csv")
        with open(self.mixed_path, "w", encoding="utf-8") as f:
            f.write("timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n")
            # Row 1: Valid
            f.write("2023-01-01T12:00:00,192.168.1.1,10.0.0.1,12345,8333,mixed_1,addr1,addr3,1.5,1.4,0.1,p2pkh\n")
            # Row 2: Missing timestamp
            f.write(",192.168.1.1,10.0.0.1,12345,8333,mixed_2,addr1,addr3,1.5,1.4,0.1,p2pkh\n")
            # Row 3: Duplicate TXID (mixed_1)
            f.write("2023-01-01T12:00:00,192.168.1.1,10.0.0.1,12345,8333,mixed_1,addr1,addr3,1.5,1.4,0.1,p2pkh\n")
            # Row 4: Malformed monetary ("invalid_num")
            f.write("2023-01-01T12:00:00,192.168.1.1,10.0.0.1,12345,8333,mixed_3,addr1,addr3,invalid_num,1.4,0.1,p2pkh\n")

    def tearDown(self):
        self.test_dir.cleanup()
        self.conn.close()

    def test_1_csv_ingestion(self):
        meta = self.loader.load_file("run_csv", self.csv_path)
        self.assertEqual(meta.record_count, 1)
        self.assertEqual(meta.quarantine_count, 0)

    def test_2_json_ingestion(self):
        meta = self.loader.load_file("run_json", self.json_path)
        self.assertEqual(meta.record_count, 1)
        self.assertEqual(meta.quarantine_count, 0)

    def test_3_xml_ingestion(self):
        meta = self.loader.load_file("run_xml", self.xml_path)
        self.assertEqual(meta.record_count, 1)
        self.assertEqual(meta.quarantine_count, 0)

    def test_4_jsonl_ingestion(self):
        meta = self.loader.load_file("run_jsonl", self.jsonl_path)
        self.assertEqual(meta.record_count, 1)
        self.assertEqual(meta.quarantine_count, 0)

    def test_5_mixed_records(self):
        meta = self.loader.load_file("run_mixed", self.mixed_path)
        
        # 6. Correct quarantine count
        self.assertEqual(meta.quarantine_count, 3)
        # 7. Correct accepted count
        self.assertEqual(meta.record_count, 1)
        
        # 8, 9, 10. Correct provenance propagation
        raw_rec = self.conn.execute("SELECT run_id, source_file, source_row FROM raw_records WHERE run_id='run_mixed'").fetchone()
        self.assertEqual(raw_rec[0], "run_mixed")
        self.assertEqual(raw_rec[1], self.mixed_path)
        self.assertEqual(raw_rec[2], 1) # Row 1 was the valid one
        
        # Verify quarantine records
        quarantines = self.conn.execute("SELECT source_row, rejection_reason FROM quarantine_errors WHERE run_id='run_mixed' ORDER BY source_row").fetchall()
        
        # Row 2: Missing timestamp
        self.assertEqual(quarantines[0][0], 2)
        self.assertIn("timestamp", quarantines[0][1].lower())
        
        # 11. Duplicate TXID behavior
        # Row 3: Duplicate txid
        self.assertEqual(quarantines[1][0], 3)
        self.assertIn("Duplicate txid", quarantines[1][1])
        
        # 12. Malformed monetary
        # Row 4: Malformed monetary data
        self.assertEqual(quarantines[2][0], 4)
        self.assertIn("Invalid monetary value", quarantines[2][1])

    def test_13_unexpected_internal_exception(self):
        # Patch the parser to simulate an unexpected internal exception (like memory error or syntax error in python)
        from unittest.mock import patch
        with patch('backend.ingestion.loader.parse_file') as mock_parse:
            mock_parse.side_effect = TypeError("Unexpected software bug")
            with self.assertRaises(TypeError):
                self.loader.load_file("run_bug", self.csv_path)

    def test_14_provenance_traceability(self):
        self.loader.load_file("run_prov", self.csv_path)
        # Verify tracing from canonical -> raw -> run
        result = self.conn.execute("""
            SELECT t.txid, r.source_row, i.source_file 
            FROM transactions t
            JOIN raw_records r ON t.run_id = r.run_id AND t.source_row = r.source_row
            JOIN ingestion_runs i ON r.run_id = i.run_id
            WHERE t.txid = 'csv_tx'
        """).fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "csv_tx")
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], self.csv_path)

    def test_15_duplicate_run_id_fails(self):
        self.loader.load_file("run_dup", self.csv_path)
        # Attempting to reuse the exact same run_id MUST fail loudly
        with self.assertRaises(duckdb.ConstraintException):
            self.loader.load_file("run_dup", self.json_path)

    def test_16_decimal_exact_persistence(self):
        self.loader.load_file("run_dec", self.csv_path)
        # The exact string in csv is "1.12345678"
        amount = self.conn.execute("SELECT amount FROM tx_inputs WHERE txid='csv_tx' AND input_index=0").fetchone()[0]
        # We fetch it and convert to string to ensure it didn't suffer float precision mutation like 1.1234567800000001
        # duckdb decimal translates back directly to python decimal 
        from decimal import Decimal
        self.assertEqual(Decimal(str(amount)), Decimal("1.12345678"))

if __name__ == '__main__':
    unittest.main()
