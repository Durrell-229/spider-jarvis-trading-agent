"""
Spider Jarvis Trading Agent — FastAPI entry point.
Default: PAPER TRADING only. Live requires explicit env confirmation.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        app=settings.app_name,
        version=settings.app_version,
        trading_mode=settings.effective_trading_mode,
        live_allowed=settings.is_live_trading_allowed,
        data_provider=settings.data_provider,
    )
    Path("logs").mkdir(exist_ok=True)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "trading_mode": settings.effective_trading_mode,
        "live_trading_enabled": settings.is_live_trading_allowed,
        "message": "Spider Jarvis — Paper Trading by default. See /api/safety",
        "docs": "/docs",
        "websocket": "/ws",
    }
