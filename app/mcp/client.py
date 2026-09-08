import logging
from typing import Dict, Any, List, Optional
from app.mcp.servers.system_mcp import system_mcp_server
from app.mcp.servers.web_mcp import web_mcp_server
from app.mcp.servers.memory_mcp import memory_mcp_server

logger = logging.getLogger("ev.mcp")

class MCPManager:
    """
    Model Context Protocol (MCP) Server Registry & Bridge.
    Connects free internal & external MCP servers (System OS, Web Search, Knowledge Store)
    and exposes their tools directly to EV Agent Core.
    """

    def __init__(self):
        self.internal_servers = {
            "system": system_mcp_server,
            "web": web_mcp_server,
            "memory": memory_mcp_server
        }

    def get_all_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """Converts all registered free MCP server tools into OpenAI function calling format."""
        openai_tools = []
        for server_name, server in self.internal_servers.items():
            tools = server.get_tools()
            for t in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": f"[{server_name.upper()} MCP TOOL] {t['description']}",
                        "parameters": t.get("parameters", {"type": "object", "properties": {}})
                    }
                })
        return openai_tools

    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Routes execution of tool call to target MCP server."""
        for server_name, server in self.internal_servers.items():
            server_tools = [t["name"] for t in server.get_tools()]
            if tool_name in server_tools:
                logger.info(f"[MCPBridge] Executing '{tool_name}' via {server_name} MCP server")
                return await server.execute_tool(tool_name, arguments)
        
        return {"error": f"MCP Tool '{tool_name}' not found"}

# Global MCP Manager Bridge
mcp_manager = MCPManager()
