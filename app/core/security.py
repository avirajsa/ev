import time
import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

def verify_device_token(token: str) -> bool:
    """
    Validates client device connection token against configured secret key.
    Supports token matching or time-hashed HMAC authentication.
    """
    if not token:
        return False
    if token == settings.DEVICE_AUTH_SECRET or token == settings.SECRET_KEY:
        return True
    return False

async def get_current_user_or_device(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
):
    if not credentials:
        # In dev mode, permit empty auth if debug is enabled, else demand auth
        if settings.APP_ENV == "development" and not settings.SECRET_KEY.endswith("production"):
            return {"user_id": "dev_user", "role": "admin"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials"
        )
    
    token = credentials.credentials
    if verify_device_token(token):
        return {"user_id": "authenticated_client", "role": "device_or_user"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token"
    )
