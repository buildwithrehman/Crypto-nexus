import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import duckdb

from backend.schema import IPEnrichment
from backend.enrichment.geoip import GeoIPEnricher
from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository

class MockGeoLiteReader:
    def __init__(self, db_type):
        self.db_type = db_type

    def get(self, ip_address):
        if ip_address == "8.8.8.8":
            if self.db_type == "city":
                return {"country": {"iso_code": "US"}}
            else:
                return {"autonomous_system_number": 15169}
        elif ip_address == "2001:4860:4860::8888":
            if self.db_type == "city":
                return {"country": {"iso_code": "US"}}
            else:
                return {"autonomous_system_number": 15169}
        elif ip_address == "1.1.1.1":
            if self.db_type == "city":
                return {}
            else:
                return {}
        elif ip_address == "2.2.2.2":
            # Simulate a corrupted DB throwing an exception during get
            raise Exception("Corrupt database")
        return None

    def close(self):
        pass

class TestGeoIPEnricher(unittest.TestCase):
    @patch('os.path.exists')
    @patch('maxminddb.open_database')
    def setUp(self, mock_open_database, mock_exists):
        mock_exists.return_value = True
        
        def mock_open(path):
            if "City" in path:
                return MockGeoLiteReader("city")
            elif "ASN" in path:
                return MockGeoLiteReader("asn")
            raise ValueError(f"Unknown DB path: {path}")

        mock_open_database.side_effect = mock_open

        self.enricher = GeoIPEnricher()

    def test_valid_ipv4_lookup(self):
        result = self.enricher.enrich_ip("8.8.8.8")
        self.assertEqual(result.ip_address, "8.8.8.8")
        self.assertEqual(result.geo_country, "US")
        self.assertEqual(result.asn, "AS15169")

    def test_valid_ipv6_lookup(self):
        result = self.enricher.enrich_ip("2001:4860:4860::8888")
        self.assertEqual(result.ip_address, "2001:4860:4860::8888")
        self.assertEqual(result.geo_country, "US")
        self.assertEqual(result.asn, "AS15169")

    def test_ip_not_found(self):
        result = self.enricher.enrich_ip("3.3.3.3")
        self.assertEqual(result.ip_address, "3.3.3.3")
        self.assertIsNone(result.geo_country)
        self.assertIsNone(result.asn)

    def test_private_reserved_ip(self):
        result = self.enricher.enrich_ip("192.168.1.1")
        self.assertEqual(result.ip_address, "192.168.1.1")
        self.assertIsNone(result.geo_country)
        self.assertIsNone(result.asn)
        
        result2 = self.enricher.enrich_ip("127.0.0.1")
        self.assertIsNone(result2.geo_country)

    def test_malformed_ip(self):
        with self.assertRaises(ValueError):
            self.enricher.enrich_ip("999.999.999.999")

    def test_corrupt_db_read(self):
        # 2.2.2.2 is set to simulate a corrupt db exception
        with self.assertRaises(Exception) as context:
            self.enricher.enrich_ip("2.2.2.2")
        self.assertIn("Corrupt database", str(context.exception))

    @patch('os.path.exists')
    def test_missing_mmdb_file(self, mock_exists):
        mock_exists.return_value = False
        enricher = GeoIPEnricher()
        self.assertEqual(enricher.status, "NOT AVAILABLE")

    def test_close_methods(self):
        # Should not raise exception
        self.enricher.close()

class TestGeoIPPersistence(unittest.TestCase):
    def setUp(self):
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_persistence_of_enrichment_results(self):
        enrichment = IPEnrichment(ip_address="8.8.8.8", geo_country="US", asn="AS15169")
        ts = datetime(2023, 1, 1, 12, 0, 0)
        
        self.repo.insert_ip_enrichment(enrichment, ts)
        
        row = self.conn.execute("SELECT geo_country, asn FROM ip_enrichment WHERE ip_address='8.8.8.8'").fetchone()
        self.assertEqual(row, ("US", "AS15169"))
        
        # Test upsert updates values
        enrichment_new = IPEnrichment(ip_address="8.8.8.8", geo_country="CA", asn="AS15169")
        self.repo.insert_ip_enrichment(enrichment_new, ts)
        
        row_new = self.conn.execute("SELECT geo_country, asn FROM ip_enrichment WHERE ip_address='8.8.8.8'").fetchone()
        self.assertEqual(row_new, ("CA", "AS15169"))

    @patch('os.path.exists')
    @patch('maxminddb.open_database')
    def test_offline_guarantee_no_sockets(self, mock_open_db, mock_exists):
        # We patch socket.socket to ensure it is never instantiated.
        # This proves the enrichment uses local files and no network connections.
        import socket
        
        mock_exists.return_value = True
        mock_db = MagicMock()
        mock_db.get.return_value = None
        mock_open_db.return_value = mock_db
        
        with patch('socket.socket') as mock_socket:
            enricher = GeoIPEnricher()
            enricher.enrich_ip("1.1.1.1")
            
            enrichment = IPEnrichment(ip_address="1.1.1.1", geo_country="US", asn="AS1234")
            self.repo.insert_ip_enrichment(enrichment, datetime.utcnow())
            
            mock_socket.assert_not_called()

if __name__ == '__main__':
    unittest.main()
