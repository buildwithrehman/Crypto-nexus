import pytest
import os
import duckdb
from datetime import datetime
from backend.api.main import app, on_startup
from backend.api.dependencies import get_pipeline_repository
from backend.api.routers.runs import RUNS_DIR

def clean_dir(run_id):
    path = os.path.join(RUNS_DIR, run_id, "case.duckdb")
    if os.path.exists(path):
        os.remove(path)

def test_c24_scenarios():
    repo = get_pipeline_repository()
    
    # A. Successful worker
    run_id_a = "run_c24_a_new"
    clean_dir(run_id_a)
    repo.insert_pipeline_run(run_id_a, "RUNNING", datetime.utcnow())
    repo.conn.execute("UPDATE pipeline_runs SET worker_pid = ? WHERE run_id = ?", [999999, run_id_a])
    case_dir = os.path.join(RUNS_DIR, run_id_a)
    os.makedirs(case_dir, exist_ok=True)
    conn_a = duckdb.connect(os.path.join(case_dir, "case.duckdb"))
    from backend.database.schema import initialize_schema
    initialize_schema(conn_a)
    conn_a.execute("INSERT INTO pipeline_runs (run_id, status, start_timestamp) VALUES (?, 'COMPLETED', ?)", [run_id_a, datetime.utcnow()])
    conn_a.close()

    # B. Failed worker
    run_id_b = "run_c24_b_new"
    clean_dir(run_id_b)
    repo.insert_pipeline_run(run_id_b, "RUNNING", datetime.utcnow())
    repo.conn.execute("UPDATE pipeline_runs SET worker_pid = ? WHERE run_id = ?", [999999, run_id_b])
    case_dir_b = os.path.join(RUNS_DIR, run_id_b)
    os.makedirs(case_dir_b, exist_ok=True)
    conn_b = duckdb.connect(os.path.join(case_dir_b, "case.duckdb"))
    initialize_schema(conn_b)
    conn_b.execute("INSERT INTO pipeline_runs (run_id, status, start_timestamp) VALUES (?, 'FAILED', ?)", [run_id_b, datetime.utcnow()])
    conn_b.close()

    # E. Dead worker + RUNNING
    run_id_e = "run_c24_e_new"
    clean_dir(run_id_e)
    repo.insert_pipeline_run(run_id_e, "RUNNING", datetime.utcnow())
    repo.conn.execute("UPDATE pipeline_runs SET worker_pid = ? WHERE run_id = ?", [999999, run_id_e])
    case_dir_e = os.path.join(RUNS_DIR, run_id_e)
    os.makedirs(case_dir_e, exist_ok=True)
    conn_e = duckdb.connect(os.path.join(case_dir_e, "case.duckdb"))
    initialize_schema(conn_e)
    conn_e.execute("INSERT INTO pipeline_runs (run_id, status, start_timestamp) VALUES (?, 'RUNNING', ?)", [run_id_e, datetime.utcnow()])
    conn_e.close()

    # F. Dead worker + missing case DB
    run_id_f = "run_c24_f_new"
    clean_dir(run_id_f)
    repo.insert_pipeline_run(run_id_f, "RUNNING", datetime.utcnow())
    repo.conn.execute("UPDATE pipeline_runs SET worker_pid = ? WHERE run_id = ?", [999999, run_id_f])
    
    # Run Recovery!
    on_startup()
    
    status_a = repo.conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id_a]).fetchone()[0]
    assert status_a == "COMPLETED"

    status_b = repo.conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id_b]).fetchone()[0]
    assert status_b == "FAILED"

    status_e = repo.conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id_e]).fetchone()[0]
    assert status_e == "FAILED"

    status_f = repo.conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id_f]).fetchone()[0]
    assert status_f == "FAILED"
