import duckdb
import json
from typing import List, Tuple
from backend.schema import (
    NetworkObservation, 
    Transaction, 
    QuarantineRecord, 
    ProvenanceMetadata,
    IngestionMetadata,
    IPEnrichment,
    EntityCluster,
    ClusterMember,
    ClusteringEvidence,
    Alert,
    AlertReason,
    AlertEvidence
)

class CryptoNexusRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def insert_pipeline_run(self, run_id: str, status: str, start_timestamp) -> None:
        self.conn.execute("""
            INSERT INTO pipeline_runs (run_id, status, current_stage, start_timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (run_id) DO UPDATE SET status = EXCLUDED.status, start_timestamp = EXCLUDED.start_timestamp
        """, [run_id, status, "INITIALIZED", start_timestamp])
        
    def update_pipeline_stage(self, run_id: str, current_stage: str) -> None:
        self.conn.execute("""
            UPDATE pipeline_runs SET current_stage = ? WHERE run_id = ?
        """, [current_stage, run_id])

    def finalize_pipeline_run(self, run_id: str, status: str, end_timestamp, failed_stage: str = None, error_message: str = None) -> None:
        self.conn.execute("""
            UPDATE pipeline_runs 
            SET status = ?, end_timestamp = ?, failed_stage = ?, error_message = ?
            WHERE run_id = ?
        """, [status, end_timestamp, failed_stage, error_message, run_id])

    def insert_ingestion_run(self, meta: IngestionMetadata) -> None:
        self.conn.execute("""
            INSERT INTO ingestion_runs (run_id, source_file, ingestion_timestamp, record_count, quarantine_count)
            VALUES (?, ?, ?, ?, ?)
        """, [meta.run_id, meta.source_file, meta.ingestion_timestamp, meta.record_count, meta.quarantine_count])

    def update_ingestion_counts(self, run_id: str, record_count: int, quarantine_count: int) -> None:
        self.conn.execute("""
            UPDATE ingestion_runs 
            SET record_count = ?, quarantine_count = ?
            WHERE run_id = ?
        """, [record_count, quarantine_count, run_id])

    def insert_quarantine_record(self, record: QuarantineRecord) -> None:
        # We need to serialize the raw_data dict to JSON string for DuckDB's JSON type
        raw_json = json.dumps(record.raw_data, default=str)
        self.conn.execute("""
            INSERT INTO quarantine_errors (run_id, source_file, source_row, raw_data, rejection_reason, quarantine_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [record.run_id, record.source_file, record.source_row, raw_json, record.rejection_reason, record.quarantine_timestamp])

    def insert_ip_enrichment(self, enrichment: IPEnrichment, timestamp: str) -> None:
        self.conn.execute("""
            INSERT INTO ip_enrichment (ip_address, geo_country, asn, enrichment_timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (ip_address) DO UPDATE SET
                geo_country = EXCLUDED.geo_country,
                asn = EXCLUDED.asn,
                enrichment_timestamp = EXCLUDED.enrichment_timestamp
        """, [enrichment.ip_address, enrichment.geo_country, enrichment.asn, timestamp])

    def insert_accepted_record(self, obs: NetworkObservation, tx: Transaction, prov: ProvenanceMetadata) -> None:
        """
        Inserts all canonical models related to a single accepted record.
        Uses a transaction to ensure atomicity.
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # 1. Insert Provenance
            self.conn.execute("""
                INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
            """, [prov.run_id, prov.source_file, prov.source_row, prov.extracted_timestamp])

            # 2. Insert Transaction
            self.conn.execute("""
                INSERT INTO transactions (txid, run_id, source_file, source_row, fee, script_type)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (txid) DO NOTHING
            """, [tx.txid, prov.run_id, prov.source_file, prov.source_row, tx.fee, tx.script_type])

            # 3. Insert Network Observation
            self.conn.execute("""
                INSERT INTO network_obs (run_id, source_file, source_row, timestamp, src_ip, dst_ip, src_port, dst_port, txid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                prov.run_id, prov.source_file, prov.source_row, obs.timestamp, 
                obs.src_ip, obs.dst_ip, obs.src_port, obs.dst_port, tx.txid
            ])

            # 4. Insert Addresses and Inputs/Outputs
            for i, (addr, amount) in enumerate(zip(tx.input_addresses, tx.input_amounts)):
                self.conn.execute("INSERT INTO addresses (address) VALUES (?) ON CONFLICT DO NOTHING", [addr])
                self.conn.execute("""
                    INSERT INTO tx_inputs (txid, input_index, address, amount)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                """, [tx.txid, i, addr, amount])
                
            for i, (addr, amount) in enumerate(zip(tx.output_addresses, tx.output_amounts)):
                self.conn.execute("INSERT INTO addresses (address) VALUES (?) ON CONFLICT DO NOTHING", [addr])
                self.conn.execute("""
                    INSERT INTO tx_outputs (txid, output_index, address, amount)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                """, [tx.txid, i, addr, amount])

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def save_clustering_results(self, cluster: EntityCluster, members: list[ClusterMember], evidences: list[ClusteringEvidence]) -> None:
        """
        Saves a cluster and its members and supporting evidence atomically.
        """
        self.save_clustering_results_bulk([cluster], members, evidences)

    def save_clustering_results_bulk(self, clusters: list[EntityCluster], members: list[ClusterMember], evidences: list[ClusteringEvidence]) -> None:
        """
        Saves multiple clusters and their members and supporting evidence atomically in bulk.
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            if clusters:
                self.conn.executemany("""
                    INSERT INTO entity_clusters (cluster_id, run_id, creation_timestamp)
                    VALUES (?, ?, ?)
                    ON CONFLICT (cluster_id) DO NOTHING
                """, [[c.cluster_id, c.run_id, c.creation_timestamp] for c in clusters])
            
            if members:
                self.conn.executemany("""
                    INSERT INTO cluster_members (cluster_id, address)
                    VALUES (?, ?)
                    ON CONFLICT DO NOTHING
                """, [[m.cluster_id, m.address] for m in members])
                
            if evidences:
                # Need to filter out duplicates if evidences overlap across clusters, but they shouldn't since we collect them at the end.
                # Actually wait, ON CONFLICT DO NOTHING is not on clustering_evidence. Let's just insert them.
                self.conn.executemany("""
                    INSERT INTO clustering_evidence (txid, address_a, address_b, heuristic_name, confidence, uncertainty, run_id, source_file, source_row)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [[e.txid, e.address_a, e.address_b, e.heuristic_name, e.confidence, e.uncertainty, e.run_id, e.source_file, e.source_row] for e in evidences])
                
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def save_alerts(self, alerts: List['Alert'], reasons: List['AlertReason'], evidences: List['AlertEvidence']) -> None:
        """
        Saves alerts, reasons, and evidence atomically.
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for a in alerts:
                self.conn.execute("""
                    INSERT INTO alerts (alert_id, run_id, txid, anomaly_strength, evidential_strength_tier, operational_queue_rank, model_version, dampeners_applied)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (alert_id) DO NOTHING
                """, [a.alert_id, a.run_id, a.txid, a.anomaly_strength, a.evidential_strength_tier, a.operational_queue_rank, a.model_version, a.dampeners_applied])
                
            for r in reasons:
                self.conn.execute("""
                    INSERT INTO alert_reasons (alert_id, reason_text, signal_type, feature_name, computation_value)
                    VALUES (?, ?, ?, ?, ?)
                """, [r.alert_id, r.reason_text, r.signal_type, r.feature_name, r.computation_value])
                
            for e in evidences:
                self.conn.execute("""
                    INSERT INTO alert_evidence (
                        evidence_id, alert_id, evidence_category, provenance_type, 
                        source_file, source_row, model_version, schema_version, 
                        feature_name, underlying_evidence_references, original_value, 
                        derived_value, uncertainty_semantics
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (evidence_id) DO NOTHING
                """, [
                    e.evidence_id, e.alert_id, e.evidence_category, e.provenance_type,
                    e.source_file, e.source_row, e.model_version, e.schema_version,
                    e.feature_name, e.underlying_evidence_references, e.original_value,
                    e.derived_value, e.uncertainty_semantics
                ])
                
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def insert_transaction_record(self, tx: Transaction, prov: ProvenanceMetadata) -> None:
        """
        Inserts canonical models related to a single transaction record without network obs.
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute("""
                INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
            """, [prov.run_id, prov.source_file, prov.source_row, prov.extracted_timestamp])

            self.conn.execute("""
                INSERT INTO transactions (txid, run_id, source_file, source_row, fee, script_type)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (txid) DO NOTHING
            """, [tx.txid, prov.run_id, prov.source_file, prov.source_row, tx.fee, tx.script_type])

            for i, (addr, amount) in enumerate(zip(tx.input_addresses, tx.input_amounts)):
                self.conn.execute("INSERT INTO addresses (address) VALUES (?) ON CONFLICT DO NOTHING", [addr])
                self.conn.execute("""
                    INSERT INTO tx_inputs (txid, input_index, address, amount)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                """, [tx.txid, i, addr, amount])
                
            for i, (addr, amount) in enumerate(zip(tx.output_addresses, tx.output_amounts)):
                self.conn.execute("INSERT INTO addresses (address) VALUES (?) ON CONFLICT DO NOTHING", [addr])
                self.conn.execute("""
                    INSERT INTO tx_outputs (txid, output_index, address, amount)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                """, [tx.txid, i, addr, amount])

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def insert_observation_record(self, obs: NetworkObservation, prov: ProvenanceMetadata) -> None:
        """
        Inserts run-scoped models related to a single network observation.
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # Enforce referential integrity for TXID manually in the application layer if needed,
            # or rely on the foreign key if there's one. The prompt requires us to check txid exists.
            row = self.conn.execute("SELECT 1 FROM transactions WHERE txid = ?", [obs.txid]).fetchone()
            if not row:
                raise ValueError(f"Unknown TXID in observation: {obs.txid}")

            self.conn.execute("""
                INSERT INTO raw_records (run_id, source_file, source_row, extracted_timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
            """, [prov.run_id, prov.source_file, prov.source_row, prov.extracted_timestamp])

            self.conn.execute("""
                INSERT INTO network_obs (run_id, source_file, source_row, timestamp, src_ip, dst_ip, src_port, dst_port, txid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                prov.run_id, prov.source_file, prov.source_row, obs.timestamp, 
                obs.src_ip, obs.dst_ip, obs.src_port, obs.dst_port, obs.txid
            ])

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
