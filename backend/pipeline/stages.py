from datetime import datetime
from backend.pipeline.context import PipelineContext
from backend.enrichment.geoip import GeoIPEnricher
from backend.clustering.cih import CIHEngine, UnionFind
from backend.database.repository import CryptoNexusRepository
from backend.correlation.service import CorrelationService

class CorrelationBridge:
    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx
        self.service = CorrelationService(ctx.repo.conn)

    def run(self):
        query = "SELECT txid FROM transactions WHERE run_id = ?"
        txids = [r[0] for r in self.ctx.repo.conn.execute(query, [self.ctx.run_id]).fetchall()]
        for txid in txids:
            self.service.validate_transaction_fee(txid)
            self.service.get_tx_timeline(txid)
            self.service.get_tx_propagations(txid)
            # The tests will verify this runs via patching or side-effects if needed, 
            # but orchestrator explicitly invoking it preserves the architecture.

class GeoIPBridge:
    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx
        self.enricher = GeoIPEnricher()

    def run(self):
        query = """
            SELECT DISTINCT src_ip FROM network_obs WHERE run_id = ? AND src_ip IS NOT NULL
            UNION
            SELECT DISTINCT dst_ip FROM network_obs WHERE run_id = ? AND dst_ip IS NOT NULL
        """
        rows = self.ctx.repo.conn.execute(query, [self.ctx.run_id, self.ctx.run_id]).fetchall()
        ips = [r[0] for r in rows]

        now = datetime.utcnow().isoformat()
        for ip in ips:
            enrichment = self.enricher.enrich_ip(ip)
            self.ctx.repo.insert_ip_enrichment(enrichment, now)
        self.ctx.repo.conn.execute("UPDATE pipeline_runs SET geoip_status = ? WHERE run_id = ?", [str(self.enricher.status), self.ctx.run_id])
        self.enricher.close()

class CIHBridge:
    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx
        self.engine = CIHEngine()

    def run(self):
        query = """
            SELECT t.txid, t.run_id, t.source_file, t.source_row
            FROM transactions t
            WHERE t.run_id = ?
        """
        tx_rows = self.ctx.repo.conn.execute(query, [self.ctx.run_id]).fetchall()
        
        union_find = UnionFind()
        all_evidence = []
        now = datetime.utcnow()
        
        for tx_row in tx_rows:
            txid, r_id, s_file, s_row = tx_row
            
            in_rows = self.ctx.repo.conn.execute("SELECT address FROM tx_inputs WHERE txid = ?", [txid]).fetchall()
            input_addresses = [r[0] for r in in_rows]
            
            out_rows = self.ctx.repo.conn.execute("SELECT amount FROM tx_outputs WHERE txid = ?", [txid]).fetchall()
            output_amounts = [float(r[0]) for r in out_rows if r[0] is not None]
            
            tx_data = {
                "txid": txid,
                "input_addresses": input_addresses,
                "output_amounts": output_amounts,
                "run_id": r_id,
                "source_file": s_file,
                "source_row": s_row
            }
            
            evidence_list = self.engine.evaluate_transaction(tx_data)
            all_evidence.extend(evidence_list)
            for ev in evidence_list:
                union_find.union(ev.address_a, ev.address_b)
                
        cluster_records = union_find.generate_cluster_records(self.ctx.run_id, now)
        
        bulk_clusters = []
        bulk_members = []
        
        for ec, cm_list in cluster_records:
            bulk_clusters.append(ec)
            bulk_members.extend(cm_list)
            
        self.ctx.repo.save_clustering_results_bulk(bulk_clusters, bulk_members, all_evidence)

class AlertEvidenceBridge:
    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx

    def gather_tx_evidence_records(self, txids: list[str]) -> dict[str, list[dict]]:
        records = {txid: [] for txid in txids}
        if not txids:
            return records
            
        placeholders = ",".join(["?"] * len(txids))
        
        # 1. Network Observations
        query_net = f"""
            SELECT txid, source_file, source_row, src_ip, dst_ip
            FROM network_obs
            WHERE run_id = ? AND txid IN ({placeholders})
        """
        net_params = [self.ctx.run_id] + txids
        net_rows = self.ctx.repo.conn.execute(query_net, net_params).fetchall()
        
        for row in net_rows:
            t, sf, sr, sip, dip = row
            records[t].append({
                "category": "OBSERVED",
                "provenance_type": "DIRECT",
                "source_file": sf,
                "source_row": sr,
                "feature_name": "network_obs",
                "original_value": f"src:{sip} dst:{dip}"
            })
            
            for ip in [sip, dip]:
                if ip:
                    geoip_row = self.ctx.repo.conn.execute("SELECT asn FROM ip_enrichment WHERE ip_address = ?", [ip]).fetchone()
                    if geoip_row and not geoip_row[0]:
                        records[t].append({
                            "category": "OBSERVED",
                            "provenance_type": "DERIVED_FROM",
                            "dampener_flag": "UNRESOLVED_GEOIP",
                            "underlying_evidence_references": [f"ip_enrichment:{ip}"]
                        })
            
        # 2. CIH Clustering Evidence
        query_cih = f"""
            SELECT txid, address_a, address_b, heuristic_name, confidence, uncertainty, source_file, source_row
            FROM clustering_evidence
            WHERE run_id = ? AND txid IN ({placeholders})
        """
        cih_params = [self.ctx.run_id] + txids
        cih_rows = self.ctx.repo.conn.execute(query_cih, cih_params).fetchall()
        
        for row in cih_rows:
            t, addra, addrb, hname, conf, unc, sf, sr = row
            # CRITICAL FIX 2: Do NOT relabel derived CIH evidence as DIRECT. 
            # Preserve Phase 16 provenance invariants: DERIVED_FROM must not have source_file/source_row
            records[t].append({
                "category": "HEURISTIC",
                "provenance_type": "DERIVED_FROM", 
                "heuristic_name": hname,
                "original_value": f"{addra} - {addrb}",
                "uncertainty_semantics": unc or "None",
                "underlying_evidence_references": [f"transactions|{sf}|{sr}"]
            })

        return records
        
    def gather_tx_timestamps(self, txids: list[str]) -> dict[str, datetime]:
        if not txids:
            return {}
        placeholders = ",".join(["?"] * len(txids))
        query = f"""
            SELECT txid, MIN(timestamp)
            FROM network_obs
            WHERE run_id = ? AND txid IN ({placeholders})
            GROUP BY txid
        """
        params = [self.ctx.run_id] + txids
        rows = self.ctx.repo.conn.execute(query, params).fetchall()
        return {r[0]: r[1] for r in rows}
