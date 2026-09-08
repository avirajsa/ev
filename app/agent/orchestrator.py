import logging
import json
from typing import List, Dict, Any, Optional
from app.core.llm_router import llm_router
from app.core.device_manager import device_manager
from app.agent.prompts import SYSTEM_PERSONA_PROMPT

logger = logging.getLogger("ev.orchestrator")

class AgentOrchestrator:
    """
    EV Brain & Agent Orchestrator. Coordinates LLM reasoning, MCP tools,
    remote device execution (via device_manager), and persistent memory.
    """

    def __init__(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_connected_devices",
                    "description": "Lists all currently connected client devices (Laptops, Phones, IoT) and their capabilities.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_type": {
                                "type": "string",
                                "description": "Optional filter by device type e.g. 'laptop', 'phone', 'iot'"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_remote_device_command",
                    "description": "Executes a command or remote action on a specific connected client device (e.g. user's laptop or phone).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_device": {
                                "type": "string",
                                "description": "Target device ID or device type (e.g. 'laptop', 'phone', or exact ID)"
                            },
                            "action": {
                                "type": "string",
                                "description": "Action name to perform e.g. 'open_application', 'run_terminal_command', 'get_system_stats', 'play_sound'"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Key-value dictionary of parameters for the action"
                            }
                        },
                        "required": ["target_device", "action"]
                    }
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executes a tool call requested by EV LLM."""
        logger.info(f"[Orchestrator] Executing tool '{tool_name}' with args: {arguments}")
        
        if tool_name == "list_connected_devices":
            dev_type = arguments.get("device_type")
            return device_manager.get_devices(device_type=dev_type)

        elif tool_name == "execute_remote_device_command":
            target = arguments.get("target_device")
            action = arguments.get("action")
            params = arguments.get("parameters", {})
            
            try:
                result = await device_manager.execute_remote_command(
                    device_id=target,
                    action=action,
                    params=params
                )
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"[Orchestrator] Remote RPC failed: {e}")
                return {"status": "error", "error": str(e)}

        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    async def process_user_request(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming user request through EV's reasoning loop.
        Handles multi-turn tool invocations and returns the final response.
        """
        # Fetch active devices summary for system prompt
        active_devices = device_manager.get_devices()
        dev_summary = json.dumps(active_devices, indent=2) if active_devices else "No connected devices active."

        system_msg = {
            "role": "system",
            "content": SYSTEM_PERSONA_PROMPT.format(connected_devices_summary=dev_summary)
        }

        messages = [system_msg]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        max_turns = 5
        used_model = None

        for turn in range(max_turns):
            logger.info(f"[Orchestrator] Turn {turn + 1}/{max_turns}")
            response = await llm_router.chat_completion(
                messages=messages,
                tools=self.tools,
                preferred_model=model_override
            )

            used_model = response.get("_used_model", used_model)
            choice = response["choices"][0]
            assistant_msg = choice["message"]
            messages.append(assistant_msg)

            # Check if model wants to call tools
            tool_calls = assistant_msg.get("tool_calls")
            if not tool_calls:
                # Execution complete!
                return {
                    "response": assistant_msg.get("content", ""),
                    "model_used": used_model,
                    "chat_history": messages[1:]  # Exclude system prompt from saved history
                }

            # Handle tool calls
            for tool_call in tool_calls:
                call_id = tool_call["id"]
                fn_name = tool_call["function"]["name"]
                fn_args = json.loads(tool_call["function"]["arguments"] or "{}")

                tool_result = await self.execute_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": fn_name,
                    "content": json.dumps(tool_result)
                })

        return {
            "response": messages[-1].get("content", "Task execution finished."),
            "model_used": used_model,
            "chat_history": messages[1:]
        }

# Global Orchestrator Instance
agent_orchestrator = AgentOrchestrator()
