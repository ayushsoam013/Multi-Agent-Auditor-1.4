from fastapi import APIRouter
from app.api.v1.endpoints import health, generation, config, chat, audit, bulk_audit

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(bulk_audit.router, prefix="/bulk-audit", tags=["bulk-audit"])
