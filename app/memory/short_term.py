import logging
from typing import Dict, List, Any

logger = logging.getLogger("ev.memory.short_term")

class SessionMemory:
    """Manages short-term conversation context for active sessions."""

    def __init__(self):
        # session_id -> List[message_dict]
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({"role": role, "content": content})

    def clear_history(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_memory = SessionMemory()
