import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.device_manager import device_manager
from app.core.security import verify_device_token

logger = logging.getLogger("ev.api.websocket")

router = APIRouter()

@router.websocket("/ws/connect")
async def websocket_connect_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token for client device"),
    device_id: str = Query(..., description="Unique hardware or app instance ID"),
    device_name: str = Query("Unknown Device", description="Friendly device name"),
    device_type: str = Query("generic", description="Device type e.g. laptop, phone, iot"),
    capabilities: str = Query("[]", description="JSON list of client capabilities")
):
    """
    Real-Time Full-Duplex WebSocket Endpoint for EV Client Devices (Laptops, Mobile Apps, IoT).
    Maintains persistent RPC connection for remote execution and event streaming.
    """
    if not verify_device_token(token):
        logger.warning(f"[WebSocket] Unauthorized connection attempt from device {device_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    try:
        parsed_caps = json.loads(capabilities) if capabilities else []
    except Exception:
        parsed_caps = []

    dev = await device_manager.register_device(
        websocket=websocket,
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        capabilities=parsed_caps
    )

    # Send registration confirmation ack
    await websocket.send_text(json.dumps({
        "type": "registration_ack",
        "status": "connected",
        "device_id": dev.device_id,
        "message": f"Welcome to EV Network, {dev.device_name}"
    }))

    try:
        while True:
            data_str = await websocket.receive_text()
            device_manager.handle_incoming_message(device_id=device_id, message_str=data_str)
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Disconnected device: {device_name} ({device_id})")
        device_manager.unregister_device(device_id)
    except Exception as e:
        logger.error(f"[WebSocket] Exception in session {device_id}: {e}")
        device_manager.unregister_device(device_id)
