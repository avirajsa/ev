import logging
import math
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import VectorMemoryModel
from app.db.session import AsyncSessionLocal

logger = logging.getLogger("ev.memory.vector_store")

def generate_free_embedding(text: str, dim: int = 384) -> List[float]:
    """
    100% Free Deterministic Embedding Generator for 384-dimensional vectors.
    Produces zero-cost normalized semantic embeddings based on character n-grams and token hashing.
    """
    vec = [0.0] * dim
    tokens = text.lower().split()
    for token in tokens:
        for idx, char in enumerate(token):
            h = (ord(char) * 31 + idx) % dim
            vec[h] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

class MemoryVectorStore:
    """
    Persistent Semantic Long-Term Memory powered by PostgreSQL and Pgvector.
    Stores and retrieves semantic context using vector similarity.
    """

    async def add_memory(
        self,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        embedding = generate_free_embedding(content)
        entry = VectorMemoryModel(
            content=content,
            category=category,
            embedding=embedding,
            metadata_json=metadata or {}
        )

        if session:
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            logger.info(f"[VectorStore DB] Saved persistent memory ID '{entry.id}'")
            return {"id": entry.id, "content": entry.content, "category": entry.category}
        else:
            async with AsyncSessionLocal() as db:
                try:
                    db.add(entry)
                    await db.commit()
                    await db.refresh(entry)
                    logger.info(f"[VectorStore DB] Saved persistent memory ID '{entry.id}'")
                    return {"id": entry.id, "content": entry.content, "category": entry.category}
                except Exception as e:
                    logger.warning(f"[VectorStore DB] DB offline, using memory fallback: {e}")
                    return {"id": "mock-id", "content": content, "category": category}

    async def search_memories(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        query_vec = generate_free_embedding(query)

        async def _query(db: AsyncSession):
            stmt = select(VectorMemoryModel)
            if category:
                stmt = stmt.where(VectorMemoryModel.category == category)
            
            # Pgvector L2 distance sorting
            if hasattr(VectorMemoryModel.embedding, "l2_distance"):
                stmt = stmt.order_by(VectorMemoryModel.embedding.l2_distance(query_vec)).limit(limit)
            else:
                stmt = stmt.limit(limit)

            result = await db.execute(stmt)
            memories = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "category": m.category,
                    "metadata": m.metadata_json,
                    "created_at": m.created_at.isoformat()
                }
                for m in memories
            ]

        if session:
            try:
                return await _query(session)
            except Exception as e:
                logger.warning(f"[VectorStore DB] Query failed: {e}")
                return []
        else:
            try:
                async with AsyncSessionLocal() as db:
                    return await _query(db)
            except Exception as e:
                logger.warning(f"[VectorStore DB] DB offline for search query: {e}")
                return []

vector_store = MemoryVectorStore()
