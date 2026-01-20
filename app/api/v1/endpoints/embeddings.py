from fastapi import APIRouter
from app.models.dtos import EmbeddingRequest, EmbeddingResponse, BatchEmbeddingRequest, BatchEmbeddingResponse

router = APIRouter()

@router.post("/generate", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    from app.services.llm_manager import llm_manager
    service = llm_manager.get_embedding_service()
    vector = service.generate_embedding(request.text, request.dimension)
    return EmbeddingResponse(vector=vector)

@router.post("/generate/batch", response_model=BatchEmbeddingResponse)
async def generate_batch_embeddings(request: BatchEmbeddingRequest):
    from app.services.llm_manager import llm_manager
    service = llm_manager.get_embedding_service()
    vectors = service.generate_batch_embeddings(request.texts, request.dimension)
    return BatchEmbeddingResponse(vectors=vectors)
