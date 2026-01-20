from fastapi import APIRouter, Query
from typing import List, Optional, Any
from app.repositories.qdrant_repo import qdrant_repo

router = APIRouter()

@router.get("/")
async def fetch_items(
    collection_name: str = Query(..., description="Name of the Qdrant collection"),
    limit: int = Query(10, description="Number of items to fetch"),
    with_payload: bool = True,
    with_vectors: bool = False
):
    points, next_page_offset = qdrant_repo.fetch_all(
        collection_name=collection_name,
        limit=limit,
        with_payload=with_payload,
        with_vectors=with_vectors
    )
    
    # Transform points to a more JSON-serializable format if needed
    results = []
    for point in points:
        results.append({
            "id": point.id,
            "payload": point.payload,
            "vector": point.vector if with_vectors else None
        })
        
    return {
        "items": results,
        "next_page_offset": next_page_offset
    }
