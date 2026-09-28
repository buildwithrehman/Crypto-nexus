import unittest
import networkx as nx
from decimal import Decimal
import pandas as pd
import numpy as np

from backend.graph.algorithms import GraphAlgorithms
from backend.ml.features import FeatureEngineer

class MockRepo:
    def __init__(self, fees=None):
        self.fees = fees or {}
        
    class MockConn:
        def __init__(self, fees):
            self.fees = fees
        def execute(self, q, params=None):
            class MockCursor:
                def __init__(self, f):
                    self.f = f
                def fetchall(self):
                    return [(k, v) for k, v in self.f.items()]
            return MockCursor(self.fees)
            
    @property
    def conn(self):
        return self.MockConn(self.fees)

class TestFeatureEngineer(unittest.TestCase):
    def setUp(self):
        self.G = nx.MultiDiGraph()
        
        # Add transactions
        self.G.add_node("tx_full", type="Transaction")
        self.G.add_node("tx_iso", type="Transaction")
        self.G.add_node("tx_no_fee", type="Transaction")
        
        # Add IP and Addresses
        self.G.add_node("IP1", type="IP")
        self.G.add_node("Addr1", type="Address")
        self.G.add_node("Addr2", type="Address")
        
        # Edges for tx_full
        self.G.add_edge("IP1", "tx_full", edge_type="PROPAGATED", timestamp="2024-01-01T10:00:00Z")
        self.G.add_edge("IP1", "tx_full", edge_type="PROPAGATED", timestamp="2024-01-01T10:05:00Z")
        
        self.G.add_edge("Addr1", "tx_full", edge_type="INPUT", amount=Decimal('5.0'))
        self.G.add_edge("tx_full", "Addr2", edge_type="OUTPUT", amount=Decimal('4.9'))
        
        # Edges for tx_no_fee
        self.G.add_edge("Addr1", "tx_no_fee", edge_type="INPUT", amount=Decimal('2.0'))
        
        # Initialize Algo and FeatureEngineer
        self.algo = GraphAlgorithms(self.G)
        
        # Mock Repo provides fee for tx_full, but NOT for tx_no_fee
        self.repo = MockRepo({"tx_full": Decimal('0.1')})
        self.fe = FeatureEngineer(self.algo, repo=self.repo)
        
    def test_build_transaction_features_exact_contract(self):
        df = self.fe.build_transaction_features()
        
        # We have 3 transactions
        self.assertEqual(len(df), 3)
        
        # Exact Column Contract
        expected_columns = [
            "tx_id",
            "in_degree", "out_degree", "total_degree",
            "betweenness", "louvain_community", "is_peel_chain",
            "weighted_in", "weighted_out", "weighted_total", "fee",
            "average_input_value", "average_output_value",
            "unique_in_addresses", "unique_out_addresses",
            "unique_ip_propagators", "propagation_edge_count",
            "duration_active_seconds"
        ]
        self.assertEqual(list(df.columns), expected_columns)
        

    def test_betweenness_approximation_parameter(self):
        import backend.ml.features as features_module
        from unittest.mock import patch
        
        self.assertEqual(features_module.BETWEENNESS_K, 1000)
        self.assertEqual(features_module.BETWEENNESS_SEED, 42)
        
        with patch.object(self.algo, 'compute_betweenness_centrality', return_value={"tx_full": 0.5, "tx_iso": 0.0, "tx_no_fee": 0.1, "tx_repeat": 0.0, "tx_missing_amt": 0.0}) as mock_bc:
            df = self.fe.build_transaction_features()
            mock_bc.assert_called_once_with(k=1000, seed=42)
            
            # verify feature name remains 'betweenness' and vector shape remains unchanged
            self.assertIn("betweenness", df.columns)
            self.assertEqual(len(df.columns), 18)  # 1 tx_id + 17 features
            
            # verify deterministic output is preserved
            df2 = self.fe.build_transaction_features()
            import pandas as pd
            pd.testing.assert_frame_equal(df, df2)

    def test_fee_semantics(self):
        df = self.fe.build_transaction_features()
        
        tx_full = df[df["tx_id"] == "tx_full"].iloc[0]
        self.assertAlmostEqual(tx_full["fee"], 0.1) # Supplied
        
        tx_no_fee = df[df["tx_id"] == "tx_no_fee"].iloc[0]
        # Missing fee MUST be None/NaN, not falsely derived from inputs - outputs (2.0 - 0 = 2.0)
        self.assertTrue(pd.isna(tx_no_fee["fee"]))
        # missing canonical fee != zero fee
        self.assertNotEqual(tx_no_fee["fee"], 0.0)
        
    def test_average_and_monetary_semantics(self):
        df = self.fe.build_transaction_features()
        tx_full = df[df["tx_id"] == "tx_full"].iloc[0]
        
        self.assertEqual(tx_full["weighted_in"], 5.0)
        self.assertEqual(tx_full["weighted_out"], 4.9)
        self.assertEqual(tx_full["weighted_total"], 9.9)
        
        # 1 input address with 5.0
        self.assertEqual(tx_full["average_input_value"], 5.0)
        # 1 output address with 4.9
        self.assertEqual(tx_full["average_output_value"], 4.9)
        
        tx_iso = df[df["tx_id"] == "tx_iso"].iloc[0]
        self.assertEqual(tx_iso["average_input_value"], 0.0)
        self.assertEqual(tx_iso["average_output_value"], 0.0)
        
    def test_repeated_input_address_behavior(self):
        # average-value denominator semantics: intentional CryptoNexus feature is average per UNIQUE address
        self.G.add_node("tx_repeat", type="Transaction")
        self.G.add_node("AddrRepeat", type="Address")
        # Add 2 edges from the same address to tx_repeat
        self.G.add_edge("AddrRepeat", "tx_repeat", edge_type="INPUT", amount=Decimal('3.0'))
        self.G.add_edge("AddrRepeat", "tx_repeat", edge_type="INPUT", amount=Decimal('2.0'))
        
        df = self.fe.build_transaction_features()
        tx_repeat = df[df["tx_id"] == "tx_repeat"].iloc[0]
        
        self.assertEqual(tx_repeat["weighted_in"], 5.0)
        self.assertEqual(tx_repeat["unique_in_addresses"], 1)
        
        # average_input_value should be weighted_in (5.0) / unique_in_addresses (1) = 5.0
        self.assertEqual(tx_repeat["average_input_value"], 5.0)

    def test_missing_monetary_amounts(self):
        self.G.add_node("tx_missing_amt", type="Transaction")
        self.G.add_node("AddrMissingAmt", type="Address")
        # Edge without 'amount'
        self.G.add_edge("AddrMissingAmt", "tx_missing_amt", edge_type="INPUT")
        
        df = self.fe.build_transaction_features()
        tx_miss = df[df["tx_id"] == "tx_missing_amt"].iloc[0]
        
        self.assertEqual(tx_miss["weighted_in"], 0.0)
        self.assertEqual(tx_miss["unique_in_addresses"], 1)
        self.assertEqual(tx_miss["average_input_value"], 0.0)

    def test_louvain_categorical_handling(self):
        # We enforce in documentation that it MUST be categorical, but we test that the returned 
        # dataframe contains it as an integer, and assert its type doesn't get coerced to float
        df = self.fe.build_transaction_features()
        self.assertTrue(pd.api.types.is_integer_dtype(df["louvain_community"]))
        
    def test_deterministic_transaction_ordering(self):
        # Insert nodes in reverse order and shuffle edge additions to test if DataFrame rows are sorted by txid
        G2 = nx.MultiDiGraph()
        G2.add_node("tx_Z", type="Transaction")
        G2.add_node("tx_A", type="Transaction")
        G2.add_node("tx_M", type="Transaction")
        
        algo2 = GraphAlgorithms(G2)
        fe2 = FeatureEngineer(algo2)
        df = fe2.build_transaction_features()
        
        tx_ids = df["tx_id"].tolist()
        self.assertEqual(tx_ids, ["tx_A", "tx_M", "tx_Z"])
        
    def test_missing_data_behavior(self):
        df = self.fe.build_transaction_features()
        tx_iso = df[df["tx_id"] == "tx_iso"].iloc[0]
        
        self.assertEqual(tx_iso["in_degree"], 0)
        self.assertEqual(tx_iso["unique_ip_propagators"], 0)
        self.assertEqual(tx_iso["propagation_edge_count"], 0)
        self.assertEqual(tx_iso["duration_active_seconds"], 0.0)
        self.assertEqual(tx_iso["is_peel_chain"], 0)
        
    def test_deterministic_output(self):
        df1 = self.fe.build_transaction_features()
        df2 = self.fe.build_transaction_features()
        pd.testing.assert_frame_equal(df1, df2)

if __name__ == '__main__':
    unittest.main()
