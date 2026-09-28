from fastapi import APIRouter, Depends, Query, HTTPException
from backend.api.dependencies import get_repository, get_db_connection
from backend.database.repository import CryptoNexusRepository
from backend.api.schemas.api_models import SearchResponse, SearchResult
from typing import List
import os
import duckdb

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=SearchResponse)
def search_records(
    q: str = Query(..., min_length=1, description="Search query"),
    category: str = Query("ALL", description="Category: ALL, TRANSACTION, ALERT, RUN"),
    limit: int = Query(50, ge=1, le=100),
    run_id: str = Query(None, description="Scope to run_id"),
    repo: CryptoNexusRepository = Depends(get_repository)
):
    results: List[SearchResult] = []
    master_conn = repo.conn
    
    # Resolve the correct connection for analytical data
    analytic_conn = master_conn
    if run_id:
        row = master_conn.execute("SELECT run_id, status FROM pipeline_runs WHERE run_id = ?", [run_id]).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        db_run_id, status = row
        case_id = "DEMO_V1" if db_run_id == "run_e2e_phase_b" else db_run_id
        if status in ["COMPLETED"]:
            if case_id != "DEMO_V1":
                case_db_path = os.path.join(os.getcwd(), "data", "runs", run_id, "case.duckdb")
                if os.path.exists(case_db_path):
                    analytic_conn = duckdb.connect(case_db_path, read_only=True)
                else:
                    analytic_conn = None
        else:
            analytic_conn = None # No analytical data available yet

    safe_q = f"%{q}%"
    
    if analytic_conn and category in ["ALL", "TRANSACTION"]:
        tx_query = "SELECT txid, run_id FROM transactions WHERE txid LIKE ?"
        params = [safe_q]
        if run_id:
            tx_query += " AND run_id = ?"
            params.append(run_id)
        tx_query += " LIMIT ?"
        params.append(limit)
        
        try:
            for row in analytic_conn.execute(tx_query, params).fetchall():
                results.append(SearchResult(
                    record_type="TRANSACTION",
                    primary_identifier=row[0],
                    display_name=f"TX: {row[0][:8]}...",
                    run_id=row[1],
                    txid=row[0]
                ))
        except Exception:
            pass
            
    if analytic_conn and category in ["ALL", "ALERT"]:
        al_query = "SELECT alert_id, run_id, txid FROM alerts WHERE alert_id LIKE ? OR txid LIKE ?"
        params = [safe_q, safe_q]
        if run_id:
            al_query += " AND run_id = ?"
            params.append(run_id)
        al_query += " LIMIT ?"
        params.append(limit)
        
        try:
            for row in analytic_conn.execute(al_query, params).fetchall():
                results.append(SearchResult(
                    record_type="ALERT",
                    primary_identifier=row[0],
                    display_name=f"ALERT: {row[0][:8]}...",
                    run_id=row[1],
                    txid=row[2],
                    alert_id=row[0]
                ))
        except Exception:
            pass
            
    # Always search RUN in master DB
    if category in ["ALL", "RUN"]:
        r_query = "SELECT run_id, status FROM pipeline_runs WHERE run_id LIKE ?"
        params = [safe_q]
        if run_id:
            r_query += " AND run_id = ?"
            params.append(run_id)
        r_query += " LIMIT ?"
        params.append(limit)
        
        for row in master_conn.execute(r_query, params).fetchall():
            results.append(SearchResult(
                record_type="RUN",
                primary_identifier=row[0],
                display_name=f"RUN: {row[0][:8]}...",
                run_id=row[0]
            ))
            
    if analytic_conn and analytic_conn != master_conn:
        analytic_conn.close()

    results = results[:limit]
    return SearchResponse(query=q, results=results, limit=limit)
