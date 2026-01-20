from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_manager import llm_manager

router = APIRouter()

class ProviderUpdate(BaseModel):
    provider: str

@router.post("/provider")
async def set_llm_provider(update: ProviderUpdate):
    try:
        llm_manager.set_provider(update.provider)
        return {"status": "success", "provider": update.provider}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/provider")
async def get_llm_provider():
    return {"provider": llm_manager.get_current_provider()}
