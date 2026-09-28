from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.dependencies import get_case_repository
from backend.api.services.query_service import QueryService
from backend.database.repository import CryptoNexusRepository
from backend.api.schemas.api_models import PaginatedResponse, AlertDetail

router = APIRouter(prefix="/runs/{run_id}/alerts", tags=["Alerts"])

@router.get("", response_model=PaginatedResponse)
def list_alerts(run_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), repo: CryptoNexusRepository = Depends(get_case_repository)):
    svc = QueryService(repo)
    data, total = svc.list_alerts(run_id, limit, offset)
    return PaginatedResponse(limit=limit, offset=offset, total=total, data=data)

@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(run_id: str, alert_id: str, repo: CryptoNexusRepository = Depends(get_case_repository)):
    svc = QueryService(repo)
    detail = svc.get_alert_detail(run_id, alert_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Alert not found in this run")
    return detail
