from typing import Optional
from datetime import datetime
from backend.pipeline.context import PipelineContext
from backend.pipeline.stages import GeoIPBridge, CorrelationBridge, CIHBridge, AlertEvidenceBridge

from backend.ingestion.loader import IngestionLoader
from backend.graph.builder import GraphBuilder
from backend.graph.algorithms import GraphAlgorithms
from backend.ml.features import FeatureEngineer
from backend.ml.pipeline import MLPipeline
from backend.scoring.alerts import AlertEngine
from backend.scoring.runner import fetch_tx_input_clusters

class PipelineOrchestrator:
    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx
        self.current_stage = "INITIALIZED"
        self.executed_stages = []

    def _set_stage(self, stage: str):
        self.current_stage = stage
        self.executed_stages.append(stage)
        self.ctx.repo.update_pipeline_stage(self.ctx.run_id, stage)

    def run(self):
        try:
            start_time = datetime.utcnow()
            self.ctx.repo.insert_pipeline_run(self.ctx.run_id, "RUNNING", start_time)
            
            # 1. INGEST
            self._set_stage("INGEST")
            loader = IngestionLoader(self.ctx.repo)
            import json
            try:
                # Check if source_file is a structured JSON config
                source_config = json.loads(self.ctx.source_file)
                if isinstance(source_config, dict) and "transactions" in source_config and "observations" in source_config:
                    loader.load_transaction_file(self.ctx.run_id, source_config["transactions"])
                    loader.load_observation_file(self.ctx.run_id, source_config["observations"])
                else:
                    loader.load_file(self.ctx.run_id, self.ctx.source_file)
            except (json.JSONDecodeError, TypeError):
                loader.load_file(self.ctx.run_id, self.ctx.source_file)
            
            # 2. GEOIP
            self._set_stage("GEOIP")
            GeoIPBridge(self.ctx).run()
            
            # 3. CORRELATION
            self._set_stage("CORRELATION")
            CorrelationBridge(self.ctx).run()
            
            # 4. CIH CLUSTERING
            self._set_stage("CIH")
            CIHBridge(self.ctx).run()
            
            # 5. GRAPH
            self._set_stage("GRAPH")
            builder = GraphBuilder(self.ctx.repo.conn)
            G = builder.build_multidigraph(run_id=self.ctx.run_id)
            
            # 6. GRAPH ANALYSIS & FEATURES
            self._set_stage("GRAPH_ANALYSIS")
            algo = GraphAlgorithms(G)
            
            self._set_stage("FEATURES")
            engineer = FeatureEngineer(algo, self.ctx.repo)
            df_features = engineer.build_transaction_features()
            
            if df_features.empty:
                self._set_stage("FINALIZE")
                self.ctx.repo.finalize_pipeline_run(self.ctx.run_id, "COMPLETED", datetime.utcnow())
                return
                
            # 7. ML SCORING
            self._set_stage("ML_SCORING")
            ml_pipeline = MLPipeline(artifact_dir=self.ctx.get_run_artifact_dir())
            
            if self.ctx.is_training_run:
                ml_results = ml_pipeline.fit_transform(df_features)
            else:
                ml_pipeline.load_artifacts()
                ml_results = ml_pipeline.transform_predict(df_features)
                
            # 8. ALERTS
            self._set_stage("ALERTS")
            alert_bridge = AlertEvidenceBridge(self.ctx)
            anomalous_txids = ml_results[ml_results["is_anomaly"] == 1]["tx_id"].tolist()
            
            tx_timestamps = alert_bridge.gather_tx_timestamps(anomalous_txids)
            tx_evidence_records = alert_bridge.gather_tx_evidence_records(anomalous_txids)
            tx_input_clusters = fetch_tx_input_clusters(self.ctx.repo, self.ctx.run_id, anomalous_txids)
            
            alert_engine = AlertEngine(
                run_id=self.ctx.run_id, 
                model_version=self.ctx.model_version,
                artifact_dir=self.ctx.get_run_artifact_dir()
            )
            
            alerts, reasons, evidences = alert_engine.generate_alerts(
                ml_results=ml_results,
                df_features=df_features,
                tx_timestamps=tx_timestamps,
                tx_evidence_records=tx_evidence_records,
                tx_input_clusters=tx_input_clusters
            )
            
            self.ctx.repo.save_alerts(alerts, reasons, evidences)
            
            # 9. FINALIZE
            self._set_stage("FINALIZE")
            # Verify Invariants
            ingestion_exists = self.ctx.repo.conn.execute("SELECT COUNT(*) FROM ingestion_runs WHERE run_id = ?", [self.ctx.run_id]).fetchone()[0] > 0
            if not ingestion_exists:
                raise ValueError("Finalize failed: run_id does not exist in ingestion_runs")
                
            expected_alerts = (ml_results["is_anomaly"] == 1).sum()
            actual_alerts = len(alerts)
            if expected_alerts != actual_alerts:
                raise ValueError(f"Finalize failed: Expected {expected_alerts} alerts, got {actual_alerts}")
                
            for alert in alerts:
                # verify alert belongs to current run (through its txid presence in network_obs for this run)
                net_obs_exists = self.ctx.repo.conn.execute("SELECT 1 FROM network_obs WHERE txid = ? AND run_id = ?", [alert.txid, self.ctx.run_id]).fetchone()
                if not net_obs_exists:
                    raise ValueError(f"Finalize failed: Alert {alert.alert_id} belongs to foreign run")
                    
            for ev in evidences:
                if ev.provenance_type == "DIRECT" and (ev.source_file is None or ev.source_row is None):
                    raise ValueError(f"Finalize failed: DIRECT evidence {ev.evidence_id} missing source_file/source_row")
                if ev.provenance_type == "DERIVED_FROM" and (ev.source_file is not None or ev.source_row is not None):
                    raise ValueError(f"Finalize failed: DERIVED_FROM evidence {ev.evidence_id} contains source_file/source_row")
                    
            self.ctx.repo.finalize_pipeline_run(self.ctx.run_id, "COMPLETED", datetime.utcnow())
            
        except Exception as e:
            self.ctx.repo.finalize_pipeline_run(self.ctx.run_id, "FAILED", datetime.utcnow(), failed_stage=self.current_stage, error_message=str(e))
            raise

