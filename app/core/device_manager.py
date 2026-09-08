import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("ev.device_manager")

class ConnectedDevice:
    def __init__(self, device_id: str, device_name: str, device_type: str, websocket: WebSocket, capabilities: list):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type  # e.g., "laptop", "phone", "iot"
        self.websocket = websocket
        self.capabilities = capabilities  # e.g., ["gui_automation", "terminal", "file_system", "camera"]
        self.pending_rpcs: Dict[str, asyncio.Future] = {}

class DeviceManager:
    """
    WebSocket Hub and Remote RPC Dispatcher for EV Client Devices (Laptops, Phones, IoT).
    Maintains full-duplex persistent connections and routes commands to remote nodes.
    """

    def __init__(self):
        # device_id -> ConnectedDevice
        self.active_devices: Dict[str, ConnectedDevice] = {}

    async def register_device(
        self,
        websocket: WebSocket,
        device_id: str,
        device_name: str,
        device_type: str,
        capabilities: list
    ) -> ConnectedDevice:
        """Registers a new connected device socket."""
        # If existing connection, close old
        if device_id in self.active_devices:
            logger.info(f"[DeviceManager] Replacing existing connection for device {device_id}")
            try:
                await self.active_devices[device_id].websocket.close()
            except Exception:
                pass

        device = ConnectedDevice(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            websocket=websocket,
            capabilities=capabilities
        )
        self.active_devices[device_id] = device
        logger.info(f"[DeviceManager] Device registered: {device_name} ({device_type}, ID: {device_id})")
        return device

    def unregister_device(self, device_id: str):
        if device_id in self.active_devices:
            device = self.active_devices.pop(device_id)
            # Fail any pending RPC futures
            for request_id, future in device.pending_rpcs.items():
                if not future.done():
                    future.set_exception(ConnectionError(f"Device {device_id} disconnected during RPC"))
            logger.info(f"[DeviceManager] Device unregistered: {device.device_name} ({device_id})")

    def get_devices(self, device_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Returns list of connected active devices."""
        devices = {}
        for dev_id, dev in self.active_devices.items():
            if device_type is None or dev.device_type == device_type:
                devices[dev_id] = {
                    "device_id": dev.device_id,
                    "device_name": dev.device_name,
                    "device_type": dev.device_type,
                    "capabilities": dev.capabilities
                }
        return devices

    async def execute_remote_command(
        self,
        device_id: str,
        action: str,
        params: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Dispatches a remote command to a connected client device (e.g. laptop)
        and waits for the client response via WebSocket RPC.
        """
        if device_id not in self.active_devices:
            # Check if there is any device matching by type (e.g. "laptop")
            target_device = None
            for dev in self.active_devices.values():
                if dev.device_type == device_id or dev.device_id == device_id:
                    target_device = dev
                    break
            if not target_device:
                raise ValueError(f"No active connected device found matching '{device_id}'")
        else:
            target_device = self.active_devices[device_id]

        request_id = str(uuid.uuid4())
        payload = {
            "type": "rpc_request",
            "request_id": request_id,
            "action": action,
            "params": params
        }

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        target_device.pending_rpcs[request_id] = future

        try:
            await target_device.websocket.send_text(json.dumps(payload))
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            target_device.pending_rpcs.pop(request_id, None)
            raise TimeoutError(f"RPC request to device '{target_device.device_name}' timed out after {timeout}s")
        except Exception as e:
            target_device.pending_rpcs.pop(request_id, None)
            raise e

    def handle_incoming_message(self, device_id: str, message_str: str):
        """Processes incoming WebSocket RPC response frames from client devices."""
        device = self.active_devices.get(device_id)
        if not device:
            return

        try:
            data = json.loads(message_str)
            msg_type = data.get("type")

            if msg_type == "rpc_response":
                request_id = data.get("request_id")
                future = device.pending_rpcs.pop(request_id, None)
                if future and not future.done():
                    if data.get("status") == "success":
                        future.set_result(data.get("result", {}))
                    else:
                        future.set_exception(RuntimeError(data.get("error", "Remote RPC execution failed")))
            elif msg_type == "ping":
                # Respond with pong
                asyncio.create_task(device.websocket.send_text(json.dumps({"type": "pong"})))

        except Exception as e:
            logger.error(f"[DeviceManager] Error processing frame from {device_id}: {e}")

# Global Device Manager Instance
device_manager = DeviceManager()
