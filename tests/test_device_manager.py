import pytest
import asyncio
import json
from unittest.mock import AsyncMock
from app.core.device_manager import DeviceManager

@pytest.mark.asyncio
async def test_device_registration_and_rpc():
    mgr = DeviceManager()
    mock_ws = AsyncMock()
    
    # 1. Register mock laptop device
    dev = await mgr.register_device(
        websocket=mock_ws,
        device_id="laptop-1",
        device_name="My MacBook",
        device_type="laptop",
        capabilities=["terminal", "gui"]
    )
    
    devices = mgr.get_devices()
    assert "laptop-1" in devices
    assert devices["laptop-1"]["device_name"] == "My MacBook"

    # 2. Simulate RPC dispatch in background task
    async def simulate_laptop_response():
        await asyncio.sleep(0.05)
        # Inspect what was sent
        assert mock_ws.send_text.called
        sent_payload = json.loads(mock_ws.send_text.call_args[0][0])
        req_id = sent_payload["request_id"]
        
        # Feed back successful RPC response
        mgr.handle_incoming_message(
            "laptop-1",
            json.dumps({
                "type": "rpc_response",
                "request_id": req_id,
                "status": "success",
                "result": {"output": "Spotify opened"}
            })
        )

    task = asyncio.create_task(simulate_laptop_response())

    # 3. Execute command via DeviceManager
    result = await mgr.execute_remote_command(
        device_id="laptop-1",
        action="open_application",
        params={"app_name": "Spotify"}
    )

    await task
    assert result == {"output": "Spotify opened"}

    # 4. Unregister device
    mgr.unregister_device("laptop-1")
    assert "laptop-1" not in mgr.get_devices()
