from fastapi import APIRouter
from app.api.v1.endpoints import health, embeddings, items, generation, config, chat

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
