from fastapi import APIRouter
from app.api.v1.agent import router as agent_router
from app.api.v1.devices import router as devices_router
from app.api.v1.memory import router as memory_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(agent_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(memory_router)
