import pytest
import os
from app.mcp.servers.system_mcp import system_mcp_server
from app.mcp.servers.web_mcp import web_mcp_server
from app.mcp.servers.memory_mcp import MemoryMCPServer
from app.mcp.client import mcp_manager

@pytest.mark.asyncio
async def test_system_mcp_telemetry():
    res = await system_mcp_server.execute_tool("get_system_telemetry", {})
    assert "cpu" in res
    assert "memory" in res
    assert "disk" in res

@pytest.mark.asyncio
async def test_system_mcp_file_io():
    test_file = "test_mcp_file.txt"
    # Write
    w_res = await system_mcp_server.execute_tool("write_system_file", {
        "file_path": test_file,
        "content": "Hello EV MCP Server"
    })
    assert w_res["status"] == "success"

    # Read
    r_res = await system_mcp_server.execute_tool("read_system_file", {"file_path": test_file})
    assert r_res["content"] == "Hello EV MCP Server"

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

@pytest.mark.asyncio
async def test_memory_mcp_server():
    mem_server = MemoryMCPServer(memory_file="test_memory.json")
    
    # Store fact
    rem_res = await mem_server.execute_tool("remember_fact", {"fact": "User prefers dark themes"})
    assert rem_res["status"] == "success"

    # Recall fact
    rec_res = await mem_server.execute_tool("recall_facts", {"query": "dark"})
    assert len(rec_res["facts"]) >= 1
    assert "dark themes" in rec_res["facts"][0]["fact"]

    # Cleanup
    if os.path.exists("test_memory.json"):
        os.remove("test_memory.json")

@pytest.mark.asyncio
async def test_mcp_manager_tool_definitions():
    tools = mcp_manager.get_all_mcp_tool_definitions()
    tool_names = [t["function"]["name"] for t in tools]
    
    assert "get_system_telemetry" in tool_names
    assert "search_duckduckgo" in tool_names
    assert "remember_fact" in tool_names
