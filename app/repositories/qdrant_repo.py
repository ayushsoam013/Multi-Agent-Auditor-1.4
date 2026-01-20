from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings

class QdrantRepository:
    def __init__(self):
        if settings.ENVIRONMENT.lower() == "prod":
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )

    def upsert_data(self, collection_name: str, points: List[models.PointStruct]):
        return self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def fetch_all(self, collection_name: str, limit: int = 100, with_payload: bool = True, with_vectors: bool = False):
        return self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def search(self, collection_name: str, query_vector: List[float], limit: int = 10):
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )

    def create_collection(self, collection_name: str, vector_size: int, distance: str = "Cosine"):
        dist_map = {
            "Cosine": models.Distance.COSINE,
            "Dot": models.Distance.DOT,
            "Euclid": models.Distance.EUCLID
        }
        
        return self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=dist_map.get(distance, models.Distance.COSINE)),
        )

    def health_check(self) -> bool:
        try:
            # Try to get collections as a simple health check
            self.client.get_collections()
            return True
        except Exception:
            return False

qdrant_repo = QdrantRepository()
