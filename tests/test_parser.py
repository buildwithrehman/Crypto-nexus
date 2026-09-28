import unittest
import os
import tempfile
from backend.ingestion.parser import detect_format, parse_file

class TestMultiFormatIngestion(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        
        self.expected_dict = {
            "timestamp": "2023-01-01T12:00:00",
            "src_ip": "192.168.1.1",
            "dst_ip": "10.0.0.1",
            "src_port": "12345",
            "dst_port": "8333",
            "txid": "deadbeef",
            "input_addresses": ["addr1", "addr2"],
            "output_addresses": ["addr3"],
            "input_amounts": ["1.5", "2.0"],
            "output_amounts": ["3.4"],
            "fee": "0.1",
            "script_type": "p2pkh"
        }

        # Create CSV
        self.csv_path = os.path.join(self.test_dir.name, "data.csv")
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n")
            f.write("2023-01-01T12:00:00,192.168.1.1,10.0.0.1,12345,8333,deadbeef,addr1;addr2,addr3,1.5;2.0,3.4,0.1,p2pkh\n")

        # Create JSON
        self.json_path = os.path.join(self.test_dir.name, "data.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write('''[
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "src_ip": "192.168.1.1",
                    "dst_ip": "10.0.0.1",
                    "src_port": "12345",
                    "dst_port": "8333",
                    "txid": "deadbeef",
                    "input_addresses": ["addr1", "addr2"],
                    "output_addresses": ["addr3"],
                    "input_amounts": ["1.5", "2.0"],
                    "output_amounts": ["3.4"],
                    "fee": "0.1",
                    "script_type": "p2pkh"
                }
            ]''')

        # Create XML
        self.xml_path = os.path.join(self.test_dir.name, "data.xml")
        with open(self.xml_path, "w", encoding="utf-8") as f:
            f.write('''<records>
                <record>
                    <timestamp>2023-01-01T12:00:00</timestamp>
                    <src_ip>192.168.1.1</src_ip>
                    <dst_ip>10.0.0.1</dst_ip>
                    <src_port>12345</src_port>
                    <dst_port>8333</dst_port>
                    <txid>deadbeef</txid>
                    <input_addresses>
                        <item>addr1</item>
                        <item>addr2</item>
                    </input_addresses>
                    <output_addresses>
                        <item>addr3</item>
                    </output_addresses>
                    <input_amounts>
                        <item>1.5</item>
                        <item>2.0</item>
                    </input_amounts>
                    <output_amounts>
                        <item>3.4</item>
                    </output_amounts>
                    <fee>0.1</fee>
                    <script_type>p2pkh</script_type>
                </record>
            </records>''')

    def tearDown(self):
        self.test_dir.cleanup()

    def test_format_detection(self):
        self.assertEqual(detect_format(self.csv_path), "csv")
        self.assertEqual(detect_format(self.json_path), "json")
        self.assertEqual(detect_format(self.xml_path), "xml")

    def test_csv_parsing(self):
        records = list(parse_file(self.csv_path))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.expected_dict)

    def test_json_parsing(self):
        records = list(parse_file(self.json_path))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.expected_dict)

    def test_xml_parsing(self):
        records = list(parse_file(self.xml_path))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.expected_dict)

if __name__ == '__main__':
    unittest.main()
