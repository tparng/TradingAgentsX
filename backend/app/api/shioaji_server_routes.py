"""
REST endpoints to start/stop/status the shioaji sidecar HTTP server.
"""
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.shioaji_server_service import shioaji_server_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shioaji-server", tags=["Shioaji Server"])


class StartRequest(BaseModel):
    api_key:    str  = Field(..., description="Sinopac API key")
    secret_key: str  = Field(..., description="Sinopac secret key")
    simulation: bool = Field(default=True, description="Paper trading mode")


@router.post("/start")
async def start_server(req: StartRequest):
    """Start the shioaji sidecar server with user credentials."""
    try:
        result = await asyncio.to_thread(
            shioaji_server_manager.start,
            req.api_key, req.secret_key, req.simulation,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/stop")
async def stop_server():
    """Stop the shioaji sidecar server."""
    return await asyncio.to_thread(shioaji_server_manager.stop)


@router.get("/status")
async def server_status():
    """Check if the shioaji sidecar server is running."""
    return await asyncio.to_thread(shioaji_server_manager.status)
