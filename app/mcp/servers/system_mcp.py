import os
import psutil
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ev.mcp.system")

class SystemMCPServer:
    """
    100% Free Local System Automation & Telemetry MCP Server.
    Provides OS resource monitoring, process management, file I/O, and shell execution.
    """

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_system_telemetry",
                "description": "Returns current CPU, Memory, Disk, and Network usage telemetry.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_running_processes",
                "description": "Lists top active processes by CPU or memory usage.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top processes to return (default: 10)"
                        }
                    }
                }
            },
            {
                "name": "read_system_file",
                "description": "Reads contents of a local file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute or relative file path to read"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "write_system_file",
                "description": "Writes or overwrites content to a local file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute or relative file path to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "File text content"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "execute_shell_command",
                "description": "Executes a shell command on the server system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command line string to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 15)"
                        }
                    },
                    "required": ["command"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[SystemMCP] Executing tool '{tool_name}'")

        if tool_name == "get_system_telemetry":
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()

            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count_logical": psutil.cpu_count(logical=True),
                    "count_physical": psutil.cpu_count(logical=False)
                },
                "memory": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "percent_used": mem.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": disk.percent
                },
                "network": {
                    "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
                }
            }

        elif tool_name == "list_running_processes":
            limit = arguments.get("limit", 10)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Sort by CPU usage
            sorted_procs = sorted(processes, key=lambda p: p.get('cpu_percent') or 0, reverse=True)
            return {"processes": sorted_procs[:limit]}

        elif tool_name == "read_system_file":
            path = arguments.get("file_path")
            if not os.path.exists(path):
                return {"error": f"File '{path}' does not exist"}
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(50000) # limit 50kb
                return {"file_path": path, "content": content}
            except Exception as e:
                return {"error": f"Failed reading file: {str(e)}"}

        elif tool_name == "write_system_file":
            path = arguments.get("file_path")
            content = arguments.get("content", "")
            try:
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"status": "success", "message": f"File '{path}' written successfully."}
            except Exception as e:
                return {"error": f"Failed writing file: {str(e)}"}

        elif tool_name == "execute_shell_command":
            cmd = arguments.get("command")
            timeout = arguments.get("timeout", 15)
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            except subprocess.TimeoutExpired:
                return {"error": f"Command timed out after {timeout} seconds"}
            except Exception as e:
                return {"error": str(e)}

        return {"error": f"Unknown tool: {tool_name}"}

system_mcp_server = SystemMCPServer()
