import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ev.mcp")

class MCPManager:
    """
    Model Context Protocol (MCP) Server Connector.
    Registers external MCP servers (file systems, databases, custom integrations)
    and exposes their tools dynamically to EV's agent brain.
    """

    def __init__(self):
        self.registered_servers: Dict[str, Dict[str, Any]] = {}

    def register_server(self, name: str, endpoint_or_cmd: str, server_type: str = "sse"):
        self.registered_servers[name] = {
            "name": name,
            "endpoint": endpoint_or_cmd,
            "type": server_type,
            "status": "connected"
        }
        logger.info(f"[MCP] Registered MCP server '{name}' ({server_type}: {endpoint_or_cmd})")

    def list_servers(self) -> List[Dict[str, Any]]:
        return list(self.registered_servers.values())

# Global MCP Manager
mcp_manager = MCPManager()
