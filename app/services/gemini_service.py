from google import genai
from google.genai import types
from typing import List, Optional
from app.core.config import settings

class GeminiService:
    def __init__(self, model_name: str = "gemini-embedding-001"):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = model_name

    def generate_embedding(self, text: str, dimension: int = 768) -> List[float]:
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=dimension)
        )
        return result.embeddings[0].values

    def generate_batch_embeddings(self, texts: List[str], dimension: int = 768) -> List[List[float]]:
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=dimension)
        )
        return [emb.values for emb in result.embeddings]

    def health_check(self) -> bool:
        try:
            # Simple embedding to check connectivity
            self.generate_embedding("health check", dimension=1)
            return True
        except Exception:
            return False

gemini_service = GeminiService()
