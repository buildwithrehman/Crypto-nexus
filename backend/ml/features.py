import pandas as pd

BETWEENNESS_K = 1000
BETWEENNESS_SEED = 42
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

class FeatureEngineer:
    def __init__(self, algo, repo=None):
        self.algo = algo
        self.repo = repo
        
    def build_transaction_features(self) -> pd.DataFrame:
        """
        Engineers a tabular feature dataset for all Transaction nodes.
        Returns a Pandas DataFrame strictly enforcing the 17-feature canonical contract.
        
        Fee Semantics:
        - "fee" represents the observed, authoritative fee from the transaction record.
        - It explicitly DOES NOT manufacture a fee from sum(inputs) - sum(outputs) 
          unless canonical data confirms it.
        - Missing fees are represented as None (NaN in pandas), avoiding zero-inflation 
          or false economic conclusions.
        
        Monetary Semantics:
        - weighted_in/out ONLY sum verified monetary edges (INPUT/OUTPUT).
        - PROPAGATED edges (from IPs) do NOT contribute to monetary sums.
        - Conversions to float occur strictly at this ML boundary.
        
        Average Value Semantics:
        - If in_degree or out_degree is 0, average values safely return 0.0.
        
        Temporal Semantics:
        - duration_active_seconds strictly represents the delta between the earliest 
          and latest OBSERVED edge timestamps (network propagation lifecycle).
          It does NOT claim to represent block confirmation time or transaction lifetime.
        
        Louvain/Peel Semantics:
        - louvain_community is an execution-local topological ID, NOT a persistent entity ID.
        - is_peel_chain strictly flags structural peel-chain candidates (0 or 1), 
          NOT confirmed laundering or suspicion.
          
        Phase 15 ML Preprocessing Contract:
        Every feature must be processed according to this strict semantic contract before modeling:
        1. tx_id: Index/Identifier (Drop before training).
        2. in_degree: Continuous. Missing = 0.
        3. out_degree: Continuous. Missing = 0.
        4. total_degree: Continuous. Missing = 0.
        5. betweenness: Continuous. Missing = 0.0.
        6. louvain_community: Categorical (MUST be one-hot encoded or explicitly declared categorical in Tree models). NEVER scale or treat as ordinal continuous.
        7. is_peel_chain: Binary (0/1). No scaling needed. Missing = 0.
        8. weighted_in: Continuous. Missing = 0.0.
        9. weighted_out: Continuous. Missing = 0.0.
        10. weighted_total: Continuous. Missing = 0.0.
        11. fee: Continuous. Missing = NaN. Imputation behavior: MUST use median/mean SimpleImputer and optionally generate a missingness indicator (fee_is_missing).
        12. average_input_value: Continuous. Missing (0 inputs) = 0.0. Representing average value per UNIQUE address.
        13. average_output_value: Continuous. Missing (0 outputs) = 0.0. Representing average value per UNIQUE address.
        14. unique_in_addresses: Continuous. Missing = 0.
        15. unique_out_addresses: Continuous. Missing = 0.
        16. unique_ip_propagators: Continuous. Missing = 0.
        17. propagation_edge_count: Continuous. Missing = 0.
        18. duration_active_seconds: Continuous. Missing = 0.0.
        """
        # 1. Compute Base Graph Metrics
        degree_metrics = self.algo.compute_degree_metrics()
        bc_metrics = self.algo.compute_betweenness_centrality(k=BETWEENNESS_K, seed=BETWEENNESS_SEED)
        temporal_metrics = self.algo.compute_temporal_metrics()
        louvain_partition = self.algo.compute_louvain_communities(random_state=42)
        peel_chains = self.algo.detect_peel_chains(min_length=2)
        
        # Build set of peel chain TXs for O(1) lookup
        peel_txs = set()
        for chain in peel_chains:
            for tx in chain:
                peel_txs.add(tx)
                
        # Query canonical fees if repo is provided
        tx_fees = {}
        if self.repo is not None:
            try:
                for row in self.repo.conn.execute("SELECT txid, fee FROM transactions").fetchall():
                    tx_fees[row[0]] = row[1]
            except Exception:
                pass
                
        # 2. Extract Transactions deterministically
        transactions = sorted([n for n, d in self.algo.G.nodes(data=True) if d.get('type') == 'Transaction'])
        
        features_list = []
        
        for tx in transactions:
            row = {"tx_id": tx}
            
            # --- Graph/Structural Features (3) ---
            deg = degree_metrics.get(tx, {})
            row["in_degree"] = deg.get("in_degree", 0)
            row["out_degree"] = deg.get("out_degree", 0)
            row["total_degree"] = deg.get("total_degree", 0)
            
            # --- Behavioral/Macro Features (3) ---
            row["betweenness"] = bc_metrics.get(tx, 0.0)
            row["louvain_community"] = louvain_partition.get(tx, -1)
            row["is_peel_chain"] = 1 if tx in peel_txs else 0
            
            # --- Monetary Features (4) ---
            w_in = deg.get("weighted_in_degree", Decimal('0'))
            w_out = deg.get("weighted_out_degree", Decimal('0'))
            w_total = deg.get("weighted_total_degree", Decimal('0'))
            
            row["weighted_in"] = float(w_in)
            row["weighted_out"] = float(w_out)
            row["weighted_total"] = float(w_total)
            
            # Fee semantics: Do NOT blindly compute w_in - w_out
            canonical_fee = tx_fees.get(tx)
            if canonical_fee is not None:
                row["fee"] = float(canonical_fee)
            else:
                row["fee"] = None
            
            # --- Network/Entity Divergence Features (4) ---
            ip_propagators = set()
            in_addresses = set()
            out_addresses = set()
            prop_count = 0
            
            for u, v, data in self.algo.G.in_edges(tx, data=True):
                e_type = data.get("edge_type")
                if e_type == "PROPAGATED":
                    ip_propagators.add(u)
                    prop_count += 1
                elif e_type == "INPUT":
                    in_addresses.add(u)
                    
            for u, v, data in self.algo.G.out_edges(tx, data=True):
                e_type = data.get("edge_type")
                if e_type == "OUTPUT":
                    out_addresses.add(v)
                    
            row["unique_in_addresses"] = len(in_addresses)
            row["unique_out_addresses"] = len(out_addresses)
            row["unique_ip_propagators"] = len(ip_propagators)
            row["propagation_edge_count"] = prop_count
            
            # Average monetary features (2)
            row["average_input_value"] = row["weighted_in"] / row["unique_in_addresses"] if row["unique_in_addresses"] > 0 else 0.0
            row["average_output_value"] = row["weighted_out"] / row["unique_out_addresses"] if row["unique_out_addresses"] > 0 else 0.0
            
            # --- Temporal Features (1) ---
            tm = temporal_metrics.get(tx, {})
            first_seen = tm.get("first_seen")
            last_seen = tm.get("last_seen")
            
            if first_seen is not None and last_seen is not None:
                try:
                    fs_str = first_seen.replace("Z", "")
                    ls_str = last_seen.replace("Z", "")
                    fs_dt = datetime.fromisoformat(fs_str)
                    ls_dt = datetime.fromisoformat(ls_str)
                    row["duration_active_seconds"] = float((ls_dt - fs_dt).total_seconds())
                except Exception:
                    row["duration_active_seconds"] = 0.0
            else:
                row["duration_active_seconds"] = 0.0
                
            features_list.append(row)
            
        df = pd.DataFrame(features_list)
        
        # Enforce exact contract ordering
        columns = [
            "tx_id",
            "in_degree", "out_degree", "total_degree",
            "betweenness", "louvain_community", "is_peel_chain",
            "weighted_in", "weighted_out", "weighted_total", "fee",
            "average_input_value", "average_output_value",
            "unique_in_addresses", "unique_out_addresses",
            "unique_ip_propagators", "propagation_edge_count",
            "duration_active_seconds"
        ]
        
        if not df.empty:
            df = df[columns]
        else:
            df = pd.DataFrame(columns=columns)
            
        return df
