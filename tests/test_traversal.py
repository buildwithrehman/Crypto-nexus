import unittest
import networkx as nx
from decimal import Decimal
from backend.graph.traversal import GraphTraversal

class TestGraphTraversal(unittest.TestCase):
    def setUp(self):
        self.G = nx.MultiDiGraph()
        
        # Build a synthetic Phase 9 topology
        # IP -> TX
        self.G.add_node("192.168.1.1", type="IP")
        self.G.add_node("tx1", type="Transaction")
        self.G.add_edge("192.168.1.1", "tx1", edge_type="PROPAGATED", network_role="src", run_id="r1", source_file="obs.csv", source_row=1)
        
        # Addr -> TX (Fund Flow)
        self.G.add_node("AddrA", type="Address")
        self.G.add_edge("AddrA", "tx1", edge_type="INPUT", amount=Decimal("1.5"), run_id="r1", source_file="inputs.csv", source_row=2)
        
        # TX -> Addr (Fund Flow)
        self.G.add_node("AddrB", type="Address")
        self.G.add_edge("tx1", "AddrB", edge_type="OUTPUT", amount=Decimal("1.4"), run_id="r1", source_file="outputs.csv", source_row=3)
        
        # Next hop: AddrB -> tx2 -> AddrC
        self.G.add_node("tx2", type="Transaction")
        self.G.add_node("AddrC", type="Address")
        self.G.add_edge("AddrB", "tx2", edge_type="INPUT", amount=Decimal("1.4"), run_id="r1", source_file="inputs.csv", source_row=4)
        self.G.add_edge("tx2", "AddrC", edge_type="OUTPUT", amount=Decimal("1.3"), run_id="r1", source_file="outputs.csv", source_row=5)
        
        self.traversal = GraphTraversal(self.G)

    def test_bfs_shortest_path_directed(self):
        # AddrA -> tx1 -> AddrB -> tx2 -> AddrC is a valid directed fund flow path
        path = self.traversal.bfs_shortest_path("AddrA", "AddrC", directed=True)
        self.assertEqual(path, ["AddrA", "tx1", "AddrB", "tx2", "AddrC"])

    def test_bfs_shortest_path_directed_no_reverse(self):
        # Cannot go backward against fund flow if directed=True
        path = self.traversal.bfs_shortest_path("AddrC", "AddrA", directed=True)
        self.assertEqual(path, [])

    def test_bfs_shortest_path_undirected(self):
        # CAN go backward if directed=False (forensic backtracking)
        path = self.traversal.bfs_shortest_path("AddrC", "AddrA", directed=False)
        self.assertEqual(path, ["AddrC", "tx2", "AddrB", "tx1", "AddrA"])
        
    def test_bfs_shortest_path_ip_to_addr(self):
        # IP -> tx1 -> AddrB
        path = self.traversal.bfs_shortest_path("192.168.1.1", "AddrB", directed=True)
        self.assertEqual(path, ["192.168.1.1", "tx1", "AddrB"])

    def test_bfs_edges(self):
        edges = self.traversal.bfs_edges("tx1", directed=True)
        self.assertIn(("tx1", "AddrB"), edges)
        
    def test_dfs_edges(self):
        edges = self.traversal.dfs_edges("AddrA", directed=True)
        self.assertEqual(edges, [("AddrA", "tx1"), ("tx1", "AddrB"), ("AddrB", "tx2"), ("tx2", "AddrC")])

    def test_extract_path_evidence(self):
        path = ["AddrA", "tx1", "AddrB"]
        ev = self.traversal.extract_path_evidence(path)
        self.assertEqual(len(ev), 2)
        
        # Check first edge provenance
        self.assertEqual(ev[0].source, "AddrA")
        self.assertEqual(ev[0].target, "tx1")
        self.assertEqual(ev[0].edge_type, "INPUT")
        self.assertEqual(ev[0].amount, Decimal("1.5"))
        self.assertEqual(ev[0].run_id, "r1")

        # Check second edge provenance
        self.assertEqual(ev[1].source, "tx1")
        self.assertEqual(ev[1].target, "AddrB")
        self.assertEqual(ev[1].edge_type, "OUTPUT")
        
    def test_extract_path_evidence_undirected(self):
        # Extracted backwards
        path = ["AddrB", "tx1", "AddrA"]
        ev = self.traversal.extract_path_evidence(path)
        self.assertEqual(len(ev), 2)
        
        # Ev 0: tx1 -> AddrB is output
        # Path was AddrB -> tx1, but edge is tx1 -> AddrB. Source must remain tx1!
        self.assertEqual(ev[0].source, "tx1")
        self.assertEqual(ev[0].target, "AddrB")
        self.assertEqual(ev[0].edge_type, "OUTPUT")
        
        # Ev 1: AddrA -> tx1 is input
        self.assertEqual(ev[1].source, "AddrA")
        self.assertEqual(ev[1].target, "tx1")
        self.assertEqual(ev[1].edge_type, "INPUT")
        
    def test_no_mutation_of_base_graph(self):
        edges_before = list(self.traversal.G.edges())
        path = self.traversal.bfs_shortest_path("AddrC", "AddrA", directed=False)
        edges_after = list(self.traversal.G.edges())
        self.assertEqual(edges_before, edges_after)
        
    def test_ip_network_role_preservation(self):
        path = ["192.168.1.1", "tx1"]
        ev = self.traversal.extract_path_evidence(path)
        self.assertEqual(ev[0].source, "192.168.1.1")
        self.assertEqual(ev[0].target, "tx1")
        self.assertEqual(ev[0].edge_type, "PROPAGATED")
        self.assertEqual(ev[0].network_role, "src")

if __name__ == '__main__':
    unittest.main()
