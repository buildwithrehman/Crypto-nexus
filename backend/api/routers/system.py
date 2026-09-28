from fastapi import APIRouter
from backend.api.schemas.api_models import HealthResponse

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")
