import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import main_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ev.main")

from app.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EV Cloud Backend...")
    logger.info(f"Primary LLM Model: {settings.PRIMARY_MODEL}")
    logger.info(f"LLM Fallback Chain: {settings.FALLBACK_MODELS}")
    await init_db()
    yield
    logger.info("Shutting down EV Cloud Backend...")

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="EV Omnipresent AI Assistant Cloud Backend with Multi-Device Remote Control & OpenRouter Model Failover",
    lifespan=lifespan
)

# CORS Configuration for Laptop and Mobile Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CLIENT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

app.include_router(main_router)

# Mount Web Documentation Portal
docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
if os.path.exists(docs_path):
    app.mount("/docs-site", StaticFiles(directory=docs_path, html=True), name="docs-site")

@app.get("/")
async def root_health_check():
    return {
        "status": "online",
        "system": settings.APP_NAME,
        "version": "0.1.0",
        "primary_model": settings.PRIMARY_MODEL,
        "docs_api": "/docs",
        "docs_web": "/docs-site"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
