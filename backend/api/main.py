from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from backend.api.routers import system, runs, alerts, graph, search
from backend.api.dependencies import get_pipeline_repository
from datetime import datetime
import os

app = FastAPI(docs_url=None, redoc_url=None)

# Mount static files for offline swagger
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def on_startup():
    print("Running startup recovery check...")
    repo = get_pipeline_repository()
    try:
        import duckdb
        active_runs = repo.conn.execute(
            "SELECT run_id, worker_pid FROM pipeline_runs WHERE status IN ('QUEUED', 'RUNNING')"
        ).fetchall()
        
        for run_id, pid in active_runs:
            is_alive = False
            if pid is not None:
                try:
                    os.kill(pid, 0)
                    is_alive = True
                except OSError:
                    is_alive = False
            if not is_alive:
                case_db_path = os.path.join(os.getcwd(), "data", "runs", run_id, "case.duckdb")
                healed = False
                if os.path.exists(case_db_path):
                    try:
                        case_conn = duckdb.connect(case_db_path, read_only=True)
                        row = case_conn.execute("SELECT status FROM pipeline_runs WHERE run_id = ?", [run_id]).fetchone()
                        if row:
                            case_status = row[0]
                            if case_status == "COMPLETED":
                                repo.finalize_pipeline_run(run_id, "COMPLETED", datetime.utcnow())
                                print(f"Healed orphaned run {run_id} from case DB: COMPLETED")
                                healed = True
                            elif case_status == "FAILED":
                                repo.finalize_pipeline_run(run_id, "FAILED", datetime.utcnow(), error_message="Worker reported failure in case DB but API missed callback.")
                                print(f"Healed orphaned run {run_id} from case DB: FAILED")
                                healed = True
                    except Exception as e:
                        print(f"Error reading case db for {run_id}: {e}")
                
                if not healed:
                    print(f"Reaping orphaned run: {run_id}")
                    repo.finalize_pipeline_run(
                        run_id, 
                        "FAILED", 
                        datetime.utcnow(), 
                        error_message="Worker process unexpectedly terminated before completion."
                    )
    except Exception as e:
        print(f"Failed to run recovery check: {e}")
        pass

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

api_router = APIRouter(prefix="/api")
api_router.include_router(system.router)
api_router.include_router(runs.router)
api_router.include_router(alerts.router)
api_router.include_router(graph.router)
api_router.include_router(search.router)
app.include_router(api_router)

from fastapi.responses import FileResponse
from fastapi import Request, HTTPException

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(request: Request, full_path: str):
    dist_dir = os.path.join(os.getcwd(), "frontend", "dist")
    
    file_path = os.path.join(dist_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    raise HTTPException(status_code=404, detail="Not found")
