from backend.database.repository import CryptoNexusRepository
from backend.api.schemas.api_models import RunResponse, AlertSummary, AlertDetail, AlertReasonResponse, AlertEvidenceResponse, KeyDriverResponse
from backend.scoring.interpretation import EvidenceInterpreter
import json

class QueryService:
    def __init__(self, repo: CryptoNexusRepository):
        self.repo = repo

    def get_run(self, run_id: str) -> RunResponse:
        row = self.repo.conn.execute(
            "SELECT run_id, status, current_stage, failed_stage, error_message, start_timestamp, end_timestamp, geoip_status, data_mode FROM pipeline_runs WHERE run_id = ?", 
            [run_id]
        ).fetchone()
        if not row:
            return None
        return RunResponse(
            run_id=row[0], status=row[1], current_stage=row[2], failed_stage=row[3],
            error_message=row[4], start_timestamp=row[5], end_timestamp=row[6], geoip_status=row[7], data_mode=row[8]
        )

    def list_runs(self, limit: int, offset: int):
        rows = self.repo.conn.execute(
            "SELECT run_id, status, current_stage, failed_stage, error_message, start_timestamp, end_timestamp, geoip_status, data_mode FROM pipeline_runs ORDER BY start_timestamp DESC NULLS LAST, run_id ASC LIMIT ? OFFSET ?", 
            [limit, offset]
        ).fetchall()
        total = self.repo.conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0]
        data = [
            RunResponse(run_id=r[0], status=r[1], current_stage=r[2], failed_stage=r[3],
                        error_message=r[4], start_timestamp=r[5], end_timestamp=r[6], geoip_status=r[7], data_mode=r[8])
            for r in rows
        ]
        return data, total

    def list_alerts(self, run_id: str, limit: int, offset: int):
        query = """
            SELECT alert_id, txid, anomaly_strength, evidential_strength_tier, operational_queue_rank, model_version, dampeners_applied
            FROM alerts
            WHERE run_id = ?
            ORDER BY operational_queue_rank ASC, alert_id ASC
            LIMIT ? OFFSET ?
        """
        rows = self.repo.conn.execute(query, [run_id, limit, offset]).fetchall()
        total = self.repo.conn.execute("SELECT COUNT(*) FROM alerts WHERE run_id = ?", [run_id]).fetchone()[0]
        data = []
        for r in rows:
            # DuckDB arrays might be returned as strings or lists, parse if string
            dampeners = r[6]
            if isinstance(dampeners, str):
                try: dampeners = json.loads(dampeners)
                except: dampeners = []
            
            data.append(AlertSummary(
                alert_id=r[0], txid=r[1], anomaly_strength=r[2], evidential_strength_tier=r[3],
                operational_queue_rank=r[4], model_version=r[5], dampeners_applied=dampeners or []
            ))
        return data, total

    def get_alert_detail(self, run_id: str, alert_id: str) -> AlertDetail:
        query = """
            SELECT alert_id, txid, anomaly_strength, evidential_strength_tier, operational_queue_rank, model_version, dampeners_applied
            FROM alerts
            WHERE run_id = ? AND alert_id = ?
        """
        row = self.repo.conn.execute(query, [run_id, alert_id]).fetchone()
        if not row:
            return None
        
        dampeners = row[6]
        if isinstance(dampeners, str):
            try: dampeners = json.loads(dampeners)
            except: dampeners = []
        
        # fetch reasons
        reasons_rows = self.repo.conn.execute(
            "SELECT reason_text, signal_type, feature_name, computation_value FROM alert_reasons WHERE alert_id = ?", 
            [alert_id]
        ).fetchall()
        reasons = [AlertReasonResponse(reason_text=r[0], signal_type=r[1], feature_name=r[2], computation_value=r[3]) for r in reasons_rows]
        
        # fetch evidence
        ev_rows = self.repo.conn.execute(
            "SELECT evidence_id, evidence_category, provenance_type, source_file, source_row, model_version, schema_version, feature_name, underlying_evidence_references, original_value, derived_value, uncertainty_semantics FROM alert_evidence WHERE alert_id = ?", 
            [alert_id]
        ).fetchall()
        evidences = []
        for r in ev_rows:
            refs = r[8]
            if isinstance(refs, str):
                try: refs = json.loads(refs)
                except: refs = []
            evidences.append(AlertEvidenceResponse(
                evidence_id=r[0], evidence_category=r[1], provenance_type=r[2], source_file=r[3], source_row=r[4],
                model_version=r[5], schema_version=r[6], feature_name=r[7], underlying_evidence_references=refs or [],
                original_value=r[9], derived_value=r[10], uncertainty_semantics=r[11]
            ))
            

        alert_detail = AlertDetail(
            alert_id=row[0], txid=row[1], anomaly_strength=row[2], evidential_strength_tier=row[3],
            operational_queue_rank=row[4], model_version=row[5], dampeners_applied=dampeners or [],
            reasons=reasons, evidence=evidences
        )
        
        # 1. Provide Transaction specifics if we can fetch fee
        tx_row = self.repo.conn.execute("SELECT fee FROM transactions WHERE txid = ?", [row[1]]).fetchone()
        tx_details = {"fee": tx_row[0]} if tx_row else None

        # 2. Generate explanation
        explanation = EvidenceInterpreter.generate_explanation(
            alert=alert_detail,
            reasons=alert_detail.reasons,
            evidences=alert_detail.evidence,
            tx_details=tx_details
        )
        
        # 3. Apply to detail
        alert_detail.summary = explanation["summary"]
        alert_detail.investigation_caveats = explanation["investigation_caveats"]
        alert_detail.provenance = explanation["provenance"]
        alert_detail.human_readable_lead = explanation["human_readable_lead"]
        
        alert_detail.key_drivers = [
            KeyDriverResponse(
                feature=d["feature"],
                value=d["value"],
                shap_value=d["shap_value"],
                direction=d["direction"],
                meaning=d["meaning"],
                evidence_tier=d["evidence_tier"]
            )
            for d in explanation["key_drivers"]
        ]
        
        return alert_detail

