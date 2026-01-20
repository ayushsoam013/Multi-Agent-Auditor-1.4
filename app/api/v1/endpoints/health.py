from fastapi import APIRouter, HTTPException
from app.models.dtos import HealthResponse
from app.repositories.qdrant_repo import qdrant_repo
from app.core.config import settings

router = APIRouter()

@router.get("/server", response_model=HealthResponse)
async def server_health():
    return HealthResponse(status="ok")

@router.get("/gemini", response_model=HealthResponse)
async def gemini_health():
    from app.services.llm_manager import llm_manager
    # Check generation service of active provider
    service = llm_manager.get_service()
    if service.health_check():
        return HealthResponse(status="ok", details={"provider": llm_manager.get_current_provider()})
    raise HTTPException(status_code=503, detail=f"{llm_manager.get_current_provider()} service unavailable")

@router.get("/qdrant", response_model=HealthResponse)
async def qdrant_health():
    if qdrant_repo.health_check():
        return HealthResponse(status="ok", details={"environment": settings.ENVIRONMENT})
    raise HTTPException(status_code=503, detail="Qdrant service unavailable")

@router.get("/gemini-gen", response_model=HealthResponse)
async def gemini_gen_health():
    from app.services.llm_manager import llm_manager
    service = llm_manager.get_service()
    if service.health_check():
         return HealthResponse(status="ok", details={"provider": llm_manager.get_current_provider()})
    raise HTTPException(status_code=503, detail="Service unavailable")
