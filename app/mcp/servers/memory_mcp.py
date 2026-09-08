import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ev.mcp.memory")

class MemoryMCPServer:
    """
    100% Free Persistent Knowledge & Key-Value Memory MCP Server.
    Stores and retrieves persistent user facts, preferences, and session context.
    """

    def __init__(self, memory_file: str = "ev_memory_store.json"):
        self.memory_file = memory_file
        self.memory_data: Dict[str, Any] = self._load_store()

    def _load_store(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[MemoryMCP] Error loading store: {e}")
        return {"facts": [], "key_value": {}}

    def _save_store(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, indent=2)
        except Exception as e:
            logger.error(f"[MemoryMCP] Error saving store: {e}")

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "remember_fact",
                "description": "Stores a persistent fact or user preference in EV long-term memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "Fact or preference content (e.g. 'User prefers dark mode', 'User's laptop is MacBook-Pro')"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional tag/category"
                        }
                    },
                    "required": ["fact"]
                }
            },
            {
                "name": "recall_facts",
                "description": "Searches or retrieves all persistent facts from long-term memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Optional search term to filter facts"
                        }
                    }
                }
            },
            {
                "name": "set_memory_key",
                "description": "Sets a key-value pair in persistent memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": { "type": "string" },
                        "value": { "type": "string" }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "get_memory_key",
                "description": "Gets a value by key from persistent memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": { "type": "string" }
                    },
                    "required": ["key"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MemoryMCP] Executing tool '{tool_name}'")

        if tool_name == "remember_fact":
            fact = arguments.get("fact")
            category = arguments.get("category", "general")
            entry = {"fact": fact, "category": category}
            self.memory_data["facts"].append(entry)
            self._save_store()
            return {"status": "success", "message": f"Remembered fact: '{fact}'"}

        elif tool_name == "recall_facts":
            query = arguments.get("query", "").lower()
            facts = self.memory_data["facts"]
            if query:
                facts = [f for f in facts if query in f["fact"].lower() or query in f.get("category", "").lower()]
            return {"facts": facts}

        elif tool_name == "set_memory_key":
            key = arguments.get("key")
            value = arguments.get("value")
            self.memory_data["key_value"][key] = value
            self._save_store()
            return {"status": "success", "key": key, "value": value}

        elif tool_name == "get_memory_key":
            key = arguments.get("key")
            val = self.memory_data["key_value"].get(key)
            return {"key": key, "value": val}

        return {"error": f"Unknown tool: {tool_name}"}

memory_mcp_server = MemoryMCPServer()
