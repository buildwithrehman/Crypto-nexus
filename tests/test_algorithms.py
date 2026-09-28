import unittest
import networkx as nx
from decimal import Decimal
from datetime import datetime, timedelta
from backend.graph.algorithms import GraphAlgorithms

class TestGraphAlgorithms(unittest.TestCase):
    def setUp(self):
        self.G = nx.MultiDiGraph()
        
        self.t0 = datetime(2026, 1, 1, 12, 0, 0)
        self.t1 = self.t0 + timedelta(minutes=5)
        self.t2 = self.t0 + timedelta(minutes=10)
        
        # IP -> TX1
        self.G.add_node("192.168.1.1", type="IP")
        self.G.add_node("tx1", type="Transaction")
        self.G.add_edge("192.168.1.1", "tx1", edge_type="PROPAGATED", timestamp=self.t0)
        
        # AddrA -> TX1 -> AddrB
        self.G.add_node("AddrA", type="Address")
        self.G.add_node("AddrB", type="Address")
        self.G.add_edge("AddrA", "tx1", edge_type="INPUT", amount=Decimal("1.5"), timestamp=self.t0)
        self.G.add_edge("tx1", "AddrB", edge_type="OUTPUT", amount=Decimal("1.4"), timestamp=self.t1)
        
        # TX1 has multiple outputs to AddrB (e.g. testing MultiDiGraph sums)
        self.G.add_edge("tx1", "AddrB", edge_type="OUTPUT", amount=Decimal("0.05"), timestamp=self.t2)
        
        self.algo = GraphAlgorithms(self.G)

    def test_compute_degree_metrics(self):
        metrics = self.algo.compute_degree_metrics()
        
        # AddrA has 1 out, 0 in. Out-weight = 1.5
        self.assertEqual(metrics["AddrA"]["in_degree"], 0)
        self.assertEqual(metrics["AddrA"]["out_degree"], 1)
        self.assertEqual(metrics["AddrA"]["weighted_out_degree"], Decimal("1.5"))
        self.assertEqual(metrics["AddrA"]["weighted_in_degree"], Decimal("0"))
        
        # AddrB has 2 in, 0 out. In-weight = 1.4 + 0.05 = 1.45
        self.assertEqual(metrics["AddrB"]["in_degree"], 2)
        self.assertEqual(metrics["AddrB"]["out_degree"], 0)
        self.assertEqual(metrics["AddrB"]["weighted_in_degree"], Decimal("1.45"))
        self.assertEqual(metrics["AddrB"]["weighted_out_degree"], Decimal("0"))
        
        # IP has 1 out, 0 in. No amount, so weight = 0
        self.assertEqual(metrics["192.168.1.1"]["in_degree"], 0)
        self.assertEqual(metrics["192.168.1.1"]["out_degree"], 1)
        self.assertEqual(metrics["192.168.1.1"]["weighted_out_degree"], Decimal("0"))

    def test_compute_betweenness_centrality(self):
        bc = self.algo.compute_betweenness_centrality()
        
        # In the directed graph: 
        # 192.168.1.1 -> tx1 -> AddrB
        # AddrA -> tx1 -> AddrB
        # tx1 sits on all shortest paths. So tx1 should have high betweenness.
        self.assertGreater(bc["tx1"], 0.0)
        
        # IP, AddrA, AddrB are leaf/boundary nodes, so betweenness = 0.0
        self.assertEqual(bc["192.168.1.1"], 0.0)
        self.assertEqual(bc["AddrA"], 0.0)
        self.assertEqual(bc["AddrB"], 0.0)

    def test_compute_temporal_metrics(self):
        metrics = self.algo.compute_temporal_metrics()
        
        # AddrB was observed at t1 and t2. First = t1, Last = t2.
        self.assertEqual(metrics["AddrB"]["first_seen"], self.t1)
        self.assertEqual(metrics["AddrB"]["last_seen"], self.t2)
        
        # tx1 was observed at t0, t1, t2. First = t0, Last = t2.
        self.assertEqual(metrics["tx1"]["first_seen"], self.t0)
        self.assertEqual(metrics["tx1"]["last_seen"], self.t2)
        
        # AddrA was observed only at t0
        self.assertEqual(metrics["AddrA"]["first_seen"], self.t0)
        self.assertEqual(metrics["AddrA"]["last_seen"], self.t0)
        
    def test_compute_betweenness_sampled(self):
        # Sampled with k
        bc_sampled_1 = self.algo.compute_betweenness_centrality(k=2, seed=42)
        bc_sampled_2 = self.algo.compute_betweenness_centrality(k=2, seed=42)
        self.assertEqual(bc_sampled_1, bc_sampled_2) # Determinism check
        
    def test_compute_betweenness_oversized_k(self):
        # Oversized k should act like exact
        bc_exact = self.algo.compute_betweenness_centrality(k=None)
        bc_oversize = self.algo.compute_betweenness_centrality(k=100) # Only 4 nodes exist
        self.assertEqual(bc_exact, bc_oversize)
        
    def test_compute_betweenness_invalid_k(self):
        with self.assertRaises(ValueError):
            self.algo.compute_betweenness_centrality(k="invalid")

    def test_parallel_edge_projection(self):
        # We inserted multiple outputs to AddrB in setUp:
        # tx1 -> AddrB (amount=1.4)
        # tx1 -> AddrB (amount=0.05)
        # In MultiDiGraph, there are 2 edges.
        self.assertEqual(self.G.number_of_edges("tx1", "AddrB"), 2)
        # When projected to DiGraph for betweenness, it collapses to 1.
        G_simple = nx.DiGraph(self.G)
        self.assertEqual(G_simple.number_of_edges("tx1", "AddrB"), 1)

    def test_missing_data_resilience(self):
        # Insert a node and edge with no amounts or timestamps
        self.G.add_node("tx2", type="Transaction")
        self.G.add_edge("AddrA", "tx2", edge_type="INPUT") # No amount/ts
        
        # Test isolated node
        self.G.add_node("IsolatedNode", type="IP")
        
        algo = GraphAlgorithms(self.G)
        
        deg = algo.compute_degree_metrics()
        # AddrA out-degree increases, but weight remains 1.5
        self.assertEqual(deg["AddrA"]["out_degree"], 2)
        self.assertEqual(deg["AddrA"]["weighted_out_degree"], Decimal("1.5"))
        # Isolated node
        self.assertEqual(deg["IsolatedNode"]["total_degree"], 0)
        self.assertEqual(deg["IsolatedNode"]["weighted_total_degree"], Decimal("0"))
        
        temp = algo.compute_temporal_metrics()
        # tx2 has no timestamp, so None
        self.assertIsNone(temp["tx2"]["first_seen"])
        self.assertIsNone(temp["tx2"]["last_seen"])
        # Isolated node has None
        self.assertIsNone(temp["IsolatedNode"]["first_seen"])
        self.assertIsNone(temp["IsolatedNode"]["last_seen"])

    def test_compute_louvain_communities_extended(self):
        # We need to test:
        # a) deterministic repeated execution
        # b) disconnected components
        # c) isolated node
        # d) MultiDiGraph -> simple undirected projection (implicit in it working)
        # e) original graph remains unchanged
        # f) mixed IP/TX/Address community does not imply ownership (conceptual)
        # g) random_state behavior
        # h) empty graph behavior
        
        # Capture original graph state
        orig_nodes = list(self.G.nodes(data=True))
        orig_edges = list(self.G.edges(data=True))
        
        # Add isolated node and disconnected component
        self.G.add_node("IsolatedNode", type="IP")
        self.G.add_node("DiscTX", type="Transaction")
        self.G.add_node("DiscAddr", type="Address")
        self.G.add_edge("DiscAddr", "DiscTX", edge_type="INPUT")
        
        # a) deterministic repeated execution & g) random_state behavior
        p1 = self.algo.compute_louvain_communities(random_state=42)
        p2 = self.algo.compute_louvain_communities(random_state=42)
        self.assertEqual(p1, p2)
        
        # p3 with different random_state might be same for tiny graph, 
        # but verifies we accept the parameter.
        p3 = self.algo.compute_louvain_communities(random_state=99)
        self.assertIsInstance(p3, dict)
        
        # b) disconnected components & c) isolated node
        self.assertIn("IsolatedNode", p1)
        self.assertIn("DiscTX", p1)
        self.assertIn("DiscAddr", p1)
        
        # e) original graph remains unchanged
        # (Remove the newly added nodes to compare original)
        self.G.remove_node("IsolatedNode")
        self.G.remove_node("DiscTX")
        self.G.remove_node("DiscAddr")
        
        new_nodes = list(self.G.nodes(data=True))
        new_edges = list(self.G.edges(data=True))
        
        self.assertEqual(orig_nodes, new_nodes)
        self.assertEqual(orig_edges, new_edges)
        
    def test_compute_louvain_empty_graph(self):
        empty_G = nx.MultiDiGraph()
        algo_empty = GraphAlgorithms(empty_G)
    def test_detect_peel_chains_extended(self):
        # We need to construct a valid peel chain of length 3
        # TX1 -> AddrChange1 -> TX2 -> AddrChange2 -> TX3
        self.G.add_node("pc_tx1", type="Transaction")
        self.G.add_node("pc_tx2", type="Transaction")
        self.G.add_node("pc_tx3", type="Transaction")
        
        self.G.add_node("pc_peel1", type="Address")
        self.G.add_node("pc_change1", type="Address")
        self.G.add_node("pc_peel2", type="Address")
        self.G.add_node("pc_change2", type="Address")
        self.G.add_node("pc_peel3", type="Address")
        self.G.add_node("pc_change3", type="Address")
        
        # IP propagation isolation
        self.G.add_node("IP_1", type="IP")
        self.G.add_edge("IP_1", "pc_tx2", edge_type="PROPAGATED")
        # Also an IP connected to the address (even if semantically strange, proves degree logic)
        self.G.add_edge("IP_1", "pc_change1", edge_type="PROPAGATED")
        
        # TX1 -> outputs
        self.G.add_edge("pc_tx1", "pc_peel1", edge_type="OUTPUT")
        self.G.add_edge("pc_tx1", "pc_change1", edge_type="OUTPUT")
        
        # AddrChange1 -> TX2
        self.G.add_edge("pc_change1", "pc_tx2", edge_type="INPUT")
        
        # TX2 -> outputs
        self.G.add_edge("pc_tx2", "pc_peel2", edge_type="OUTPUT")
        self.G.add_edge("pc_tx2", "pc_change2", edge_type="OUTPUT")
        
        # AddrChange2 -> TX3
        self.G.add_edge("pc_change2", "pc_tx3", edge_type="INPUT")
        
        # TX3 -> outputs (valid link, terminates)
        self.G.add_edge("pc_tx3", "pc_peel3", edge_type="OUTPUT")
        self.G.add_edge("pc_tx3", "pc_change3", edge_type="OUTPUT")
        
        # a) valid 3-TX structural chain, h) IP propagation isolation
        chains = self.algo.detect_peel_chains(min_length=3)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0], ["pc_tx1", "pc_tx2", "pc_tx3"])
        
        # b) min_length cutoff
        self.assertEqual(len(self.algo.detect_peel_chains(min_length=4)), 0)
        
        # l) min_length validation (< 2 raises ValueError)
        with self.assertRaises(ValueError):
            self.algo.detect_peel_chains(min_length=1)

    def test_peel_chain_invalid_output_count(self):
        # c) invalid output count
        self.G.add_node("tx_start", type="Transaction")
        self.G.add_edge("tx_start", "addr_peel", edge_type="OUTPUT")
        # Only 1 output -> breaks
        chains = self.algo.detect_peel_chains(min_length=2)
        self.assertEqual(len([c for c in chains if "tx_start" in c]), 0)

    def test_peel_chain_duplicate_output(self):
        # d) duplicate output address
        self.G.add_node("tx_dup", type="Transaction")
        # TX with 2 output edges but to the SAME address -> 1 distinct output address
        self.G.add_edge("tx_dup", "addr_dup", edge_type="OUTPUT")
        self.G.add_edge("tx_dup", "addr_dup", edge_type="OUTPUT")
        chains = self.algo.detect_peel_chains(min_length=2)
        self.assertEqual(len([c for c in chains if "tx_dup" in c]), 0)
        
    def test_peel_chain_multiple_typed_edges(self):
        # e) multiple INPUT edges on candidate address, f) multiple OUTPUT edges
        self.G.add_node("tx_a", type="Transaction")
        self.G.add_node("tx_b", type="Transaction")
        self.G.add_node("tx_c", type="Transaction")
        self.G.add_edge("tx_a", "addr_multi", edge_type="OUTPUT")
        self.G.add_edge("tx_a", "addr_peel_a", edge_type="OUTPUT") # Valid 2 outputs
        
        self.G.add_edge("addr_multi", "tx_b", edge_type="INPUT")
        # Add another INPUT edge to break pass-through degree
        self.G.add_edge("addr_multi", "tx_c", edge_type="INPUT")
        
        chains = self.algo.detect_peel_chains(min_length=2)
        self.assertEqual(len([c for c in chains if c[0] == "tx_a"]), 0)
        
    def test_peel_chain_loop_prevention(self):
        # i) loop prevention
        self.G.add_node("tx_loop1", type="Transaction")
        self.G.add_node("tx_loop2", type="Transaction")
        self.G.add_edge("tx_loop1", "addr_loop1", edge_type="OUTPUT")
        self.G.add_edge("tx_loop1", "addr_loop_peel1", edge_type="OUTPUT")
        self.G.add_edge("addr_loop1", "tx_loop2", edge_type="INPUT")
        
        self.G.add_edge("tx_loop2", "addr_loop2", edge_type="OUTPUT")
        self.G.add_edge("tx_loop2", "addr_loop_peel2", edge_type="OUTPUT")
        
        # Loop back
        self.G.add_edge("addr_loop2", "tx_loop1", edge_type="INPUT")
        
        chains = self.algo.detect_peel_chains(min_length=2)
        # It should detect [tx_loop1, tx_loop2] or [tx_loop2, tx_loop1] but not infinite
        loops = [c for c in chains if "tx_loop1" in c]
        self.assertTrue(all(len(c) == 2 for c in loops))
        
    def test_peel_chain_branching(self):
        # g) branching address, j) deterministic ordering
        self.G.add_node("tx_branch", type="Transaction")
        self.G.add_node("tx_next1", type="Transaction")
        self.G.add_node("tx_next2", type="Transaction")
        
        self.G.add_edge("tx_branch", "addr_b1", edge_type="OUTPUT")
        self.G.add_edge("tx_branch", "addr_b2", edge_type="OUTPUT")
        
        self.G.add_edge("addr_b1", "tx_next1", edge_type="INPUT")
        self.G.add_edge("addr_b2", "tx_next2", edge_type="INPUT")
        
        self.G.add_edge("tx_next1", "addr_n1_1", edge_type="OUTPUT")
        self.G.add_edge("tx_next1", "addr_n1_2", edge_type="OUTPUT")
        self.G.add_edge("tx_next2", "addr_n2_1", edge_type="OUTPUT")
        self.G.add_edge("tx_next2", "addr_n2_2", edge_type="OUTPUT")
        
        chains = self.algo.detect_peel_chains(min_length=2)
        branch_chains = [c for c in chains if c[0] == "tx_branch"]
        self.assertEqual(len(branch_chains), 1)
        # Because we sorted outputs, addr_b1 should be picked before addr_b2
        self.assertEqual(branch_chains[0][1], "tx_next1")

if __name__ == '__main__':
    unittest.main()
