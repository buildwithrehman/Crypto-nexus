import duckdb
import networkx as nx
from typing import Optional
from decimal import Decimal

class GraphBuilder:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def build_multidigraph(self, run_id: Optional[str] = None) -> nx.MultiDiGraph:
        """
        Builds an in-memory NetworkX MultiDiGraph from the canonical DuckDB records.
        If run_id is provided, strictly scopes the graph to nodes and edges originating from that run.
        Strictly enforces the semantic mapping:
        IP ──[PROPAGATED]──► TX
        Address ──[INPUT]──► TX
        TX ──[OUTPUT]──► Address
        
        Never creates IP → OWNS → Address edges.
        """
        G = nx.MultiDiGraph()
        
        where_clause = "WHERE run_id = ?" if run_id else ""
        where_params = [run_id] if run_id else []
        
        where_tr_clause = "WHERE tr.run_id = ?" if run_id else ""
        
        # 1. IP -> TX [PROPAGATED]
        # We use src_ip and dst_ip from network_obs.
        # A single observation yields an edge from src_ip -> txid and dst_ip -> txid (if available).
        obs_rows = self.conn.execute(f"""
            SELECT txid, src_ip, dst_ip, timestamp, run_id, source_file, source_row
            FROM network_obs
            {where_clause}
            ORDER BY timestamp ASC, txid ASC
        """, where_params).fetchall()
        
        for row in obs_rows:
            txid, src_ip, dst_ip, ts, r_id, src_file, src_row = row
            
            # Ensure TX node exists with type
            if not G.has_node(txid):
                G.add_node(txid, type="Transaction")
                
            if src_ip:
                if not G.has_node(src_ip):
                    G.add_node(src_ip, type="IP")
                G.add_edge(src_ip, txid, edge_type="PROPAGATED", network_role="src", timestamp=ts, run_id=r_id, source_file=src_file, source_row=src_row)
                
            if dst_ip:
                if not G.has_node(dst_ip):
                    G.add_node(dst_ip, type="IP")
                G.add_edge(dst_ip, txid, edge_type="PROPAGATED", network_role="dst", timestamp=ts, run_id=r_id, source_file=src_file, source_row=src_row)

        # 2. Address -> TX [INPUT]
        in_rows = self.conn.execute(f"""
            SELECT t.txid, t.address, t.amount, tr.run_id, tr.source_file, tr.source_row
            FROM tx_inputs t
            JOIN transactions tr ON t.txid = tr.txid
            {where_tr_clause}
            ORDER BY t.txid ASC, t.input_index ASC
        """, where_params).fetchall()
        
        for row in in_rows:
            txid, address, amount, r_id, src_file, src_row = row
            
            if not G.has_node(txid):
                G.add_node(txid, type="Transaction")
            
            if not G.has_node(address):
                G.add_node(address, type="Address")
                
            G.add_edge(address, txid, edge_type="INPUT", amount=Decimal(str(amount)) if amount is not None else None, run_id=r_id, source_file=src_file, source_row=src_row)
            
        # 3. TX -> Address [OUTPUT]
        out_rows = self.conn.execute(f"""
            SELECT t.txid, t.address, t.amount, tr.run_id, tr.source_file, tr.source_row
            FROM tx_outputs t
            JOIN transactions tr ON t.txid = tr.txid
            {where_tr_clause}
            ORDER BY t.txid ASC, t.output_index ASC
        """, where_params).fetchall()
        
        for row in out_rows:
            txid, address, amount, r_id, src_file, src_row = row
            
            if not G.has_node(txid):
                G.add_node(txid, type="Transaction")
                
            if not G.has_node(address):
                G.add_node(address, type="Address")
                
            G.add_edge(txid, address, edge_type="OUTPUT", amount=Decimal(str(amount)) if amount is not None else None, run_id=r_id, source_file=src_file, source_row=src_row)

        # Note on Clustering:
        # Per Phase 8 rules and architecture, H1/H2/CIH evidence edges are NOT automatically
        # injected into the base topological graph to prevent false-positive contamination.
        # They remain in the clustering_evidence and entity_clusters tables for higher-level analysis.
            
        return G
