import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ev.memory.vector_store")

class MemoryVectorStore:
    """
    Interface for EV's persistent semantic memory.
    Stores episodic facts, user preferences, and long-term context.
    """

    def __init__(self):
        self._mock_memories: List[Dict[str, Any]] = []

    async def add_memory(self, content: str, category: str = "general", metadata: Optional[Dict[str, Any]] = None):
        entry = {
            "content": content,
            "category": category,
            "metadata": metadata or {}
        }
        self._mock_memories.append(entry)
        logger.info(f"[VectorMemory] Saved long-term memory: '{content}'")

    async def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # In full production, this performs vector similarity search via pgvector / Chroma
        results = [m for m in self._mock_memories if any(word in m["content"].lower() for word in query.lower().split())]
        return results[:limit]

vector_store = MemoryVectorStore()
