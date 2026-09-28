import unittest
from fastapi.testclient import TestClient
from backend.api.main import app

class TestSearchAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_search_no_query(self):
        response = self.client.get("/api/search")
        self.assertEqual(response.status_code, 422)

    def test_search_txid(self):
        response = self.client.get("/api/search?q=999&category=TRANSACTION")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["limit"], 50)

    def test_search_all(self):
        response = self.client.get("/api/search?q=demo")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertIsInstance(results, list)

if __name__ == '__main__':
    unittest.main()
