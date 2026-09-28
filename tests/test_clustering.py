import unittest
from datetime import datetime
import duckdb

from backend.database.schema import initialize_schema
from backend.database.repository import CryptoNexusRepository
from backend.clustering.cih import CIHEngine, UnionFind

class TestCIHEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CIHEngine()
        self.base_tx = {
            "txid": "tx1",
            "input_addresses": ["A", "B"],
            "output_amounts": ["1.0", "2.0"],
            "run_id": "run1",
            "source_file": "file.csv",
            "source_row": 1
        }

    def test_two_input_cih(self):
        ev = self.engine.evaluate_transaction(self.base_tx)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].address_a, "A")
        self.assertEqual(ev[0].address_b, "B")
        self.assertEqual(ev[0].heuristic_name, "CIH")
        self.assertEqual(ev[0].confidence, "High")
        self.assertIsNone(ev[0].uncertainty)

    def test_three_input_cih(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B", "C"]
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(len(ev), 3) # AB, AC, BC
        pairs = {(e.address_a, e.address_b) for e in ev}
        self.assertEqual(pairs, {("A", "B"), ("A", "C"), ("B", "C")})

    def test_single_input(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A"]
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(len(ev), 0)
        
    def test_empty_input(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = []
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(len(ev), 0)

    def test_duplicate_input(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "A", "A"]
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(len(ev), 0) # Only 1 unique, so 0 pairs

    def test_coinjoin_identical_outputs(self):
        tx = self.base_tx.copy()
        tx["output_amounts"] = ["1.0", "1.0", "1.0"] # Suspicious CoinJoin pattern
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].confidence, "Low")
        self.assertIn("CoinJoin-like/collaborative", ev[0].uncertainty)
        
    def test_high_input_count(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = [f"addr{i}" for i in range(60)]
        ev = self.engine.evaluate_transaction(tx)
        self.assertEqual(ev[0].confidence, "Low")
        self.assertIn("batching", ev[0].uncertainty)

class TestUnionFind(unittest.TestCase):
    def test_transitive_union_find(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        clusters = uf.get_clusters()
        # Expect 1 cluster
        self.assertEqual(len(clusters), 1)
        root = list(clusters.keys())[0]
        self.assertEqual(sorted(clusters[root]), ["A", "B", "C"])

    def test_multiple_independent_clusters(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("C", "D")
        clusters = uf.get_clusters()
        self.assertEqual(len(clusters), 2)

    def test_deterministic_root(self):
        uf1 = UnionFind()
        uf1.union("X", "A") # A is lexically smaller, should be root
        root1 = uf1.find("X")
        self.assertEqual(root1, "A")
        
        # Test reverse insertion order
        uf2 = UnionFind()
        uf2.union("A", "X")
        root2 = uf2.find("X")
        self.assertEqual(root2, "A")

class TestClusteringPersistence(unittest.TestCase):
    def setUp(self):
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        self.repo = CryptoNexusRepository(self.conn)
        self.engine = CIHEngine()

    def test_persistence_and_determinism(self):
        tx = {
            "txid": "tx1",
            "input_addresses": ["A", "B"],
            "output_amounts": ["1.0", "2.0"],
            "run_id": "run1",
            "source_file": "file.csv",
            "source_row": 1
        }
        
        self.conn.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run1', 'file.csv', current_timestamp)")
        self.conn.execute("INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp) VALUES ('run1', 'file.csv', 1, current_timestamp)")
        self.conn.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx1', 'run1', 'file.csv', 1)")
        
        # Evaluate heuristics
        evidences = self.engine.evaluate_transaction(tx)
        
        # Union Find
        uf = UnionFind()
        for ev in evidences:
            uf.union(ev.address_a, ev.address_b)
            
        ts = datetime.utcnow()
        clusters = uf.generate_cluster_records("run1", ts)
        
        for ec, members in clusters:
            self.repo.save_clustering_results(ec, members, evidences)
            
        # Verify
        db_clusters = self.conn.execute("SELECT cluster_id FROM entity_clusters").fetchall()
        self.assertEqual(len(db_clusters), 1)
        c_id = db_clusters[0][0]
        
        db_members = self.conn.execute("SELECT address FROM cluster_members WHERE cluster_id = ? ORDER BY address", [c_id]).fetchall()
        self.assertEqual(db_members, [("A",), ("B",)])
        
        db_evidence = self.conn.execute("SELECT txid, address_a, address_b, heuristic_name FROM clustering_evidence").fetchall()
        self.assertEqual(db_evidence, [("tx1", "A", "B", "CIH")])

        # 14. Re-running the same data produces the same clusters.
        # UPSERT / DO NOTHING should safely absorb exact duplicate cluster saves
        for ec, members in clusters:
            self.repo.save_clustering_results(ec, members, evidences) # should not crash
            
        self.assertEqual(self.conn.execute("SELECT count(*) FROM entity_clusters").fetchone()[0], 1)

if __name__ == '__main__':
    unittest.main()
