import duckdb
import threading
from backend.database.connection import initialize_schema
from backend.database.repository import CryptoNexusRepository
import os

_conn = None
_lock = threading.Lock()

def get_db_connection():
    global _conn
    with _lock:
        if _conn is None:
            # We open one read-write connection for the entire application.
            # DuckDB allows concurrent cursors from multiple threads on this connection.
            db_path = os.environ.get("CRYPTONEXUS_DB_PATH", "cryptonexus.db")
            
            # PHASE C: DEMO FAST PATH
            # If the database does not exist, check for a demo seed and copy it.
            if not os.path.exists(db_path):
                seed_path = os.path.join(os.getcwd(), "demo_seed.duckdb")
                if os.path.exists(seed_path):
                    import shutil
                    import time
                    start = time.time()
                    shutil.copy(seed_path, db_path)
                    print(f"[DEMO FAST PATH] Copied demo seed in {time.time() - start:.3f}s")
            
            _conn = duckdb.connect(db_path)
            initialize_schema(_conn)
    return _conn

def get_repository():
    conn = get_db_connection()
    # In DuckDB, it's safer for concurrent threads to use their own cursor.
    cursor = conn.cursor()
    try:
        repo = CryptoNexusRepository(cursor)
        yield repo
    finally:
        cursor.close()

def get_pipeline_repository():
    # Dedicated function for background pipeline to acquire its repository
    conn = get_db_connection()
    return CryptoNexusRepository(conn.cursor())

def get_case_repository(run_id: str):
    from fastapi import HTTPException
    
    # Always query the master DB first to resolve the case
    master_conn = get_db_connection()
    row = master_conn.execute("SELECT run_id, status FROM pipeline_runs WHERE run_id = ?", [run_id]).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
        
    db_run_id, status = row
    case_id = "DEMO_V1" if db_run_id == "run_e2e_phase_b" else db_run_id
    
    # If the pipeline hasn't finished, there is no analytical data to query.
    if status in ["INITIALIZED", "QUEUED", "RUNNING"]:
        raise HTTPException(status_code=409, detail=f"Case database not ready. Run is currently {status}")
    if status == "FAILED":
        raise HTTPException(status_code=409, detail="Run failed. Case database is incomplete.")
        
    if case_id == "DEMO_V1":
        # DEMO_V1 uses the master database
        cursor = master_conn.cursor()
        try:
            yield CryptoNexusRepository(cursor)
        finally:
            cursor.close()
    else:
        # NEW_RUN uses its isolated case DB
        case_db_path = os.path.join(os.getcwd(), "data", "runs", run_id, "case.duckdb")
        if not os.path.exists(case_db_path):
            raise HTTPException(status_code=404, detail="Case database file missing")
            
        case_conn = duckdb.connect(case_db_path, read_only=True)
        cursor = case_conn.cursor()
        try:
            yield CryptoNexusRepository(cursor)
        finally:
            cursor.close()
            case_conn.close()

