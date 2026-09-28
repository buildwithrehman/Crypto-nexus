from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from backend.api.dependencies import get_repository, get_pipeline_repository
from backend.api.services.query_service import QueryService
from backend.database.repository import CryptoNexusRepository
from backend.api.schemas.api_models import RunCreateRequest, RunResponse, PaginatedResponse
from datetime import datetime
import os
import uuid
import shutil
import sys
import subprocess
import asyncio

router = APIRouter(prefix="/runs", tags=["Runs"])

DATA_DIR = os.path.join(os.getcwd(), "data")
RUNS_DIR = os.path.join(DATA_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024 # 100 MB

@router.post("", response_model=RunResponse)
def create_run(req: RunCreateRequest = None, repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    run_id = req.run_id if req and req.run_id is not None else "run_" + uuid.uuid4().hex
    
    # validate safe chars
    if not run_id or len(run_id) > 100 or not all(c.isalnum() or c in "_-." for c in run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id format")
        
    if svc.get_run(run_id):
        raise HTTPException(status_code=409, detail="Run already exists")
    repo.insert_pipeline_run(run_id, "INITIALIZED", datetime.utcnow())
    return svc.get_run(run_id)

@router.get("", response_model=PaginatedResponse)
def list_runs(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    data, total = svc.list_runs(limit, offset)
    return PaginatedResponse(limit=limit, offset=offset, total=total, data=data)

@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/{run_id}/ingest")
def ingest_file(run_id: str, file: UploadFile = File(...), repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "INITIALIZED":
        raise HTTPException(status_code=409, detail="Run must be in INITIALIZED state to ingest")
        
    ingestion_row = repo.conn.execute("SELECT 1 FROM run_uploads WHERE run_id = ?", [run_id]).fetchone()
    if ingestion_row:
        raise HTTPException(status_code=409, detail="Run has already been ingested")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.csv', '.json', '.xml']:
        raise HTTPException(status_code=422, detail="Unsupported file format")
    
    run_uploads_dir = os.path.join(RUNS_DIR, run_id, "uploads")
    os.makedirs(run_uploads_dir, exist_ok=True)
    
    safe_filename = f"{run_id}_{uuid.uuid4().hex}{ext}"
    dest_path = os.path.abspath(os.path.join(run_uploads_dir, safe_filename))
    
    if not dest_path.startswith(os.path.abspath(run_uploads_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename (path traversal)")

    size = 0
    with open(dest_path, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                buffer.close()
                os.remove(dest_path)
                raise HTTPException(status_code=413, detail="File too large")
            buffer.write(chunk)
            
    repo.conn.execute("INSERT INTO run_uploads (run_id, source_file) VALUES (?, ?)", [run_id, dest_path])
    
    return {"message": "Upload complete, ready for execution"}


# Internal API endpoint for worker to update its status safely in the master DB
from pydantic import BaseModel
from typing import Optional
class WorkerStatusUpdate(BaseModel):
    status: str
    current_stage: Optional[str] = None
    error_message: Optional[str] = None

@router.patch("/{run_id}/internal/status")
def update_worker_status(run_id: str, payload: WorkerStatusUpdate, repo: CryptoNexusRepository = Depends(get_repository)):
    if payload.status == "FAILED":
        repo.finalize_pipeline_run(run_id, "FAILED", datetime.utcnow(), failed_stage=payload.current_stage, error_message=payload.error_message)
    elif payload.status == "COMPLETED":
        repo.finalize_pipeline_run(run_id, "COMPLETED", datetime.utcnow())
    elif payload.status == "RUNNING" and payload.current_stage:
        repo.update_pipeline_stage(run_id, payload.current_stage)
    return {"status": "ok"}


def monitor_worker_process_sync(run_id: str, proc: subprocess.Popen):
    """Wait for worker synchronously in a thread, releasing the GIL."""
    proc.wait()
    
    repo = get_pipeline_repository()
    try:
        run = repo.conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id]).fetchone()
        if run and run[0] in ["RUNNING", "QUEUED"]:
            # Process died without updating status or callback failed
            case_db_path = os.path.join(RUNS_DIR, run_id, "case.duckdb")
            healed = False
            import duckdb
            if os.path.exists(case_db_path):
                try:
                    case_conn = duckdb.connect(case_db_path, read_only=True)
                    row = case_conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id]).fetchone()
                    if row:
                        if row[0] == "COMPLETED":
                            repo.finalize_pipeline_run(run_id, "COMPLETED", datetime.utcnow())
                            healed = True
                        elif row[0] == "FAILED":
                            repo.finalize_pipeline_run(run_id, "FAILED", datetime.utcnow(), error_message="Worker reported failure in case DB but API missed callback.")
                            healed = True
                except Exception as e:
                    pass
            if not healed:
                repo.finalize_pipeline_run(
                    run_id, 
                    "FAILED", 
                    datetime.utcnow(), 
                    failed_stage=None, 
                    error_message=f"Worker process exited with code {proc.returncode}"
                )
    except Exception as e:
        print(f"Failed to reap worker {run_id}: {e}")

@router.post("/{run_id}/execute", status_code=202)
def execute_pipeline(run_id: str, background_tasks: BackgroundTasks, repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status in ["RUNNING", "COMPLETED", "QUEUED"]:
        raise HTTPException(status_code=409, detail=f"Cannot execute run in state {run.status}")
        
    upload_row = repo.conn.execute("SELECT source_file FROM run_uploads WHERE run_id = ?", [run_id]).fetchone()
    if not upload_row:
        raise HTTPException(status_code=409, detail="Cannot execute before ingestion")
        
    source_file = upload_row[0]
    
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    case_db_path = os.path.join(run_dir, "case.duckdb")
    log_path = os.path.join(run_dir, "pipeline.log")
    
    log_file = open(log_path, "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "backend.worker", run_id, source_file, case_db_path],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=os.getcwd()
    )
        
    repo.conn.execute(
        "UPDATE pipeline_runs SET status = 'QUEUED', worker_pid = ? WHERE run_id = ?", 
        [proc.pid, run_id]
    )
    
    # Spawn background monitor
    background_tasks.add_task(monitor_worker_process_sync, run_id, proc)
    
    return {"message": "Pipeline queued for execution"}


@router.get("/{run_id}/stats")
def get_run_stats(run_id: str, repo: CryptoNexusRepository = Depends(get_repository)):
    svc = QueryService(repo)
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    stats = {
        "transactions": 0,
        "network_obs": 0,
        "alerts": 0,
        "alert_evidence": 0
    }
    
    if run.status == "COMPLETED":
        # Resolve case DB
        try:
            if run.is_demo:
                conn = repo.conn
            else:
                from backend.api.dependencies import get_case_repository
                case_repo = get_case_repository(run_id)
                conn = case_repo.conn
                
            stats["transactions"] = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            stats["network_obs"] = conn.execute("SELECT COUNT(*) FROM network_obs").fetchone()[0]
            stats["alerts"] = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            stats["alert_evidence"] = conn.execute("SELECT COUNT(*) FROM alert_evidence").fetchone()[0]
        except Exception:
            pass
            
    return stats
