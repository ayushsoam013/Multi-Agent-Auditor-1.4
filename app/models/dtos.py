from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class EmbeddingRequest(BaseModel):
    text: str
    dimension: int = 768

class EmbeddingResponse(BaseModel):
    vector: List[float]

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    dimension: int = 768

class BatchEmbeddingResponse(BaseModel):
    vectors: List[List[float]]

class HealthResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None

class ItemFetchRequest(BaseModel):
    collection_name: str
    limit: int = 100

class GenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class GenerationResponse(BaseModel):
    text: str
    model: str

class ChatMessage(BaseModel):
    role: str
    content: str | List[Any]

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    provider: Optional[str] = None # "gemini" or "litellm"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[TokenUsage] = None
