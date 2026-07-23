"""
REST endpoints to start/stop/status the shioaji sidecar HTTP server.
"""
import asyncio
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.shioaji_server_service import shioaji_server_manager, SIDECAR_PORT
from backend.app.db.database import get_db
from backend.app.db.models import WatchlistItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shioaji-server", tags=["Shioaji Server"])


class StartRequest(BaseModel):
    api_key:    str  = Field(..., description="Sinopac API key")
    secret_key: str  = Field(..., description="Sinopac secret key")
    simulation: bool = Field(default=True, description="Paper trading mode")
    ca_path:    str  = Field(default="", description="Path to Sinopac.pfx (required for live orders)")
    ca_passwd:  str  = Field(default="", description="CA certificate password")


@router.post("/start")
async def start_server(req: StartRequest):
    """Start the shioaji sidecar server with user credentials."""
    try:
        result = await asyncio.to_thread(
            shioaji_server_manager.start,
            req.api_key, req.secret_key, req.simulation,
            req.ca_path, req.ca_passwd,
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


SIDECAR_URL = f"http://127.0.0.1:{SIDECAR_PORT}"
LIST_NAME = "TradingAgentsX"

# Taiwan market_type → Pro Terminal exchange code
_EXCHANGE = {"twse": "TSE", "tpex": "OTC"}


@router.post("/watchlist-sync")
async def sync_watchlist_to_pro_terminal(db: AsyncSession = Depends(get_db)):
    """
    Push all TWSE/TPEx tickers from the TradingAgentsX watchlist into the
    Shioaji Pro Terminal as a named list called 'TradingAgentsX'.
    """
    # Fetch Taiwan tickers from DB
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.market_type.in_(["twse", "tpex"]))
    )
    items = result.scalars().all()

    contracts = [
        {
            "security_type": "STK",
            "exchange": _EXCHANGE[item.market_type],
            "code": item.ticker,
        }
        for item in items
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check if the "TradingAgentsX" list already exists
        try:
            r = await client.get(f"{SIDECAR_URL}/api/v1/watchlist")
            r.raise_for_status()
            lists = r.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Sidecar unreachable: {e}")

        existing = next((l for l in lists if l.get("name") == LIST_NAME), None)

        if existing:
            # Update existing list
            r = await client.put(
                f"{SIDECAR_URL}/api/v1/watchlist/{existing['id']}",
                json={"contracts": contracts},
            )
        else:
            # Create new list
            r = await client.post(
                f"{SIDECAR_URL}/api/v1/watchlist",
                json={"name": LIST_NAME, "contracts": contracts},
            )

        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Sidecar error: {r.text}")

        return {"synced": len(contracts), "list_name": LIST_NAME, "action": "updated" if existing else "created"}
