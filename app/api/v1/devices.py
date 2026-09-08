from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.device_manager import device_manager
from app.core.security import get_current_user_or_device

router = APIRouter(prefix="/devices", tags=["Devices"])

class RemoteExecuteRequest(BaseModel):
    action: str = Field(..., description="Remote action name e.g. open_app, execute_script, system_info")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    timeout: float = Field(default=30.0, description="RPC timeout in seconds")

@router.get("")
async def list_connected_devices(
    device_type: Optional[str] = None,
    current_client: dict = Depends(get_current_user_or_device)
):
    """Lists all active connected client devices (laptops, phones, IoT nodes)."""
    return {"devices": device_manager.get_devices(device_type=device_type)}

@router.post("/{device_id}/execute")
async def execute_remote_command(
    device_id: str,
    request: RemoteExecuteRequest,
    current_client: dict = Depends(get_current_user_or_device)
):
    """Directly dispatches a remote command to a connected client device."""
    try:
        result = await device_manager.execute_remote_command(
            device_id=device_id,
            action=request.action,
            params=request.parameters,
            timeout=request.timeout
        )
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except TimeoutError as te:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(te))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
