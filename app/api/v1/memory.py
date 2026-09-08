from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from app.memory.vector_store import vector_store
from app.core.security import get_current_user_or_device

router = APIRouter(prefix="/memory", tags=["Memory"])

class StoreMemoryRequest(BaseModel):
    content: str = Field(..., description="Fact, user preference, or memory content to store")
    category: str = Field(default="general", description="Memory category")
    metadata: Optional[Dict[str, Any]] = Field(default=None)

@router.post("")
async def store_memory(
    request: StoreMemoryRequest,
    current_client: dict = Depends(get_current_user_or_device)
):
    """Stores a persistent long-term memory entry."""
    await vector_store.add_memory(
        content=request.content,
        category=request.category,
        metadata=request.metadata
    )
    return {"status": "success", "message": "Memory stored persistently"}

@router.get("/search")
async def search_memory(
    q: str = Query(..., description="Query term or semantic search phrase"),
    limit: int = Query(5, ge=1, le=20),
    current_client: dict = Depends(get_current_user_or_device)
):
    """Performs semantic search across persistent long-term memories."""
    results = await vector_store.search_memories(query=q, limit=limit)
    return {"results": results}
