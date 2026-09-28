import sys
import duckdb
import urllib.request
import json
import time
from datetime import datetime
from backend.database.repository import CryptoNexusRepository
from backend.database.schema import initialize_schema
from backend.pipeline.context import PipelineContext
from backend.pipeline.orchestrator import PipelineOrchestrator

API_BASE_URL = "http://localhost:8000"

def report_status(run_id, payload):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                f"{API_BASE_URL}/api/runs/{run_id}/internal/status",
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'},
                method='PATCH'
            )
            urllib.request.urlopen(req, timeout=1)
            return
        except Exception as e:
            print(f"Worker failed to report status (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(0.1)

class WorkerRepository(CryptoNexusRepository):
    def __init__(self, conn, run_id):
        super().__init__(conn)
        self.worker_run_id = run_id

    def insert_pipeline_run(self, run_id, status, start_time):
        report_status(self.worker_run_id, {"status": "RUNNING"})
            
    def update_pipeline_stage(self, run_id, stage):
        self.conn.execute("UPDATE pipeline_runs SET current_stage = ? WHERE run_id = ?", [stage, self.worker_run_id])
        report_status(self.worker_run_id, {"status": "RUNNING", "current_stage": stage})

    def finalize_pipeline_run(self, run_id, status, end_time, failed_stage=None, error_message=None):
        self.conn.execute(
            "UPDATE pipeline_runs SET status = ?, end_timestamp = ?, failed_stage = ?, error_message = ? WHERE run_id = ?",
            [status, end_time, failed_stage, error_message, self.worker_run_id]
        )
        report_status(self.worker_run_id, {
            "status": status,
            "current_stage": failed_stage,
            "error_message": error_message
        })

def main():
    if len(sys.argv) < 4:
        print("Usage: python -m backend.worker <run_id> <source_file> <case_db_path>")
        sys.exit(1)
        
    run_id = sys.argv[1]
    source_file = sys.argv[2]
    case_db_path = sys.argv[3]
    
    print(f"[{datetime.utcnow().isoformat()}] Worker starting for run {run_id}")
    print(f"Case DB: {case_db_path}")
    
    try:
        conn = duckdb.connect(case_db_path)
        initialize_schema(conn)
        
        conn.execute("INSERT OR IGNORE INTO pipeline_runs (run_id, status, start_timestamp) VALUES (?, 'RUNNING', ?)", [run_id, datetime.utcnow()])
        conn.execute("INSERT OR IGNORE INTO run_uploads (run_id, source_file) VALUES (?, ?)", [run_id, source_file])
        
        repo = WorkerRepository(conn, run_id)
        
        ctx = PipelineContext(
            run_id=run_id,
            source_file=source_file,
            repo=repo,
            artifact_dir="backend/ml/artifacts",
            is_training_run=False
        )
        
        orchestrator = PipelineOrchestrator(ctx)
        orchestrator.run()
        
        print(f"[{datetime.utcnow().isoformat()}] Worker completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Worker crashed: {e}")
        # The orchestrator catches exceptions and calls finalize_pipeline_run. 
        # But if it fails outside orchestrator, we handle it:
        try:
            conn.execute("UPDATE pipeline_runs SET status = 'FAILED', error_message = ? WHERE run_id = ?", [str(e), run_id])
            report_status(run_id, {"status": "FAILED", "error_message": str(e)})
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
