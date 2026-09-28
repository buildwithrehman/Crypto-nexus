import unittest
import duckdb
from decimal import Decimal
from backend.database.schema import initialize_schema
from backend.graph.builder import GraphBuilder

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.conn = duckdb.connect(':memory:')
        initialize_schema(self.conn)
        
        # Insert test data
        self.conn.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run1', 'file.csv', current_timestamp)")
        self.conn.execute("INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp) VALUES ('run1', 'file.csv', 1, current_timestamp)")
        
        self.conn.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx1', 'run1', 'file.csv', 1)")
        self.conn.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx2', 'run1', 'file.csv', 1)")
        
        self.conn.execute("INSERT INTO network_obs (src_ip, src_port, dst_ip, dst_port, txid, timestamp, run_id, source_file, source_row) VALUES ('1.1.1.1', 8333, '2.2.2.2', 8333, 'tx1', current_timestamp, 'run1', 'file.csv', 1)")
        
        self.conn.execute("INSERT INTO addresses (address) VALUES ('AddrA'), ('AddrB'), ('AddrC')")
        self.conn.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx1', 0, 'AddrA', 1.5)")
        self.conn.execute("INSERT INTO tx_outputs (txid, output_index, address, amount) VALUES ('tx1', 0, 'AddrB', 1.4)")
        
        # Second tx
        self.conn.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx2', 0, 'AddrB', 1.4)")
        self.conn.execute("INSERT INTO tx_outputs (txid, output_index, address, amount) VALUES ('tx2', 0, 'AddrC', 1.3)")

    def test_build_multidigraph(self):
        builder = GraphBuilder(self.conn)
        G = builder.build_multidigraph()
        
        # Nodes: tx1, tx2, 1.1.1.1, 2.2.2.2, AddrA, AddrB, AddrC
        # Total = 7
        self.assertEqual(G.number_of_nodes(), 7)
        
        self.assertEqual(G.nodes['tx1']['type'], 'Transaction')
        self.assertEqual(G.nodes['1.1.1.1']['type'], 'IP')
        self.assertEqual(G.nodes['AddrA']['type'], 'Address')
        
        # Edges
        # IP -> TX: 1.1.1.1 -> tx1, 2.2.2.2 -> tx1
        # Addr -> TX: AddrA -> tx1, AddrB -> tx2
        # TX -> Addr: tx1 -> AddrB, tx2 -> AddrC
        # Total = 6
        self.assertEqual(G.number_of_edges(), 6)
        
        # Verify edge attributes and types
        ip_edges = G.get_edge_data('1.1.1.1', 'tx1')
        self.assertIsNotNone(ip_edges)
        self.assertEqual(ip_edges[0]['edge_type'], 'PROPAGATED')
        
        in_edges = G.get_edge_data('AddrA', 'tx1')
        self.assertIsNotNone(in_edges)
        self.assertEqual(in_edges[0]['edge_type'], 'INPUT')
        self.assertEqual(in_edges[0]['amount'], Decimal('1.5'))
        
        out_edges = G.get_edge_data('tx1', 'AddrB')
        self.assertIsNotNone(out_edges)
        self.assertEqual(out_edges[0]['edge_type'], 'OUTPUT')
        self.assertEqual(out_edges[0]['amount'], Decimal('1.4'))
        
        # No IP -> Address edges
        self.assertFalse(G.has_edge('1.1.1.1', 'AddrA'))

    def test_determinism(self):
        builder = GraphBuilder(self.conn)
        G1 = builder.build_multidigraph()
        G2 = builder.build_multidigraph()
        
        self.assertEqual(list(G1.nodes()), list(G2.nodes()))
        self.assertEqual(list(G1.edges(data=True)), list(G2.edges(data=True)))

    def test_determinism_shuffled(self):
        # Create second connection with inverted insertion order
        conn2 = duckdb.connect(':memory:')
        initialize_schema(conn2)
        
        conn2.execute("INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp) VALUES ('run1', 'file.csv', current_timestamp)")
        conn2.execute("INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp) VALUES ('run1', 'file.csv', 1, current_timestamp)")
        
        # Insert tx2 then tx1
        conn2.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx2', 'run1', 'file.csv', 1)")
        conn2.execute("INSERT INTO transactions (txid, run_id, source_file, source_row) VALUES ('tx1', 'run1', 'file.csv', 1)")
        
        # Insert addresses inverted
        conn2.execute("INSERT INTO addresses (address) VALUES ('AddrC'), ('AddrB'), ('AddrA')")
        
        # Insert outputs then inputs
        conn2.execute("INSERT INTO tx_outputs (txid, output_index, address, amount) VALUES ('tx2', 0, 'AddrC', 1.3)")
        conn2.execute("INSERT INTO tx_outputs (txid, output_index, address, amount) VALUES ('tx1', 0, 'AddrB', 1.4)")
        conn2.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx2', 0, 'AddrB', 1.4)")
        conn2.execute("INSERT INTO tx_inputs (txid, input_index, address, amount) VALUES ('tx1', 0, 'AddrA', 1.5)")
        
        # Insert network obs last
        # We need to fetch the timestamp from conn1 so they are exactly identical
        ts = self.conn.execute("SELECT timestamp FROM network_obs LIMIT 1").fetchone()[0]
        conn2.execute("INSERT INTO network_obs (src_ip, src_port, dst_ip, dst_port, txid, timestamp, run_id, source_file, source_row) VALUES ('1.1.1.1', 8333, '2.2.2.2', 8333, 'tx1', ?, 'run1', 'file.csv', 1)", [ts])
        
        builder1 = GraphBuilder(self.conn)
        builder2 = GraphBuilder(conn2)
        
        G1 = builder1.build_multidigraph()
        G2 = builder2.build_multidigraph()
        
        self.assertEqual(list(G1.nodes()), list(G2.nodes()))
        self.assertEqual(list(G1.edges(data=True)), list(G2.edges(data=True)))

if __name__ == '__main__':
    unittest.main()
