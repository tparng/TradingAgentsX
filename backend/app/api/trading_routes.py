"""
REST API endpoints for Shioaji real-time trading.
All Shioaji calls are blocking; wrapped with asyncio.to_thread() for FastAPI compatibility.
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.app.services.shioaji_service import shioaji_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trading", tags=["Trading"])


# ── Request / Response models ─────────────────────────────────────────────────

class ConnectRequest(BaseModel):
    api_key: str    = Field(..., description="Shioaji API key from Sinopac Securities")
    secret_key: str = Field(..., description="Shioaji secret key")
    simulation: bool = Field(default=True, description="Paper trading mode (default: True)")


class ConnectResponse(BaseModel):
    session_id: str
    simulation: bool
    accounts:   List[dict]
    message:    str


class PlaceOrderRequest(BaseModel):
    session_id:  str   = Field(..., description="Session ID from /connect")
    ticker:      str   = Field(..., description="Taiwan stock code, e.g. '2330'")
    action:      str   = Field(..., description="'BUY' or 'SELL'")
    price:       float = Field(..., description="Limit price (TWD)")
    quantity:    int   = Field(..., ge=1, description="Number of lots (1 lot = 1000 shares)")
    price_type:  str   = Field(default="LMT", description="'LMT' or 'MKT'")
    order_type:  str   = Field(default="ROD", description="'ROD', 'IOC', or 'FOK'")


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_session(session_id: str):
    try:
        return shioaji_manager.get_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _map_error(e: Exception, status: int = 500):
    raise HTTPException(status_code=status, detail=str(e))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/connect", response_model=ConnectResponse)
async def connect(req: ConnectRequest):
    """
    Authenticate with Shioaji and return a session_id.
    simulation=True (default) uses Sinopac's paper-trading environment.
    """
    try:
        sess = await asyncio.to_thread(
            shioaji_manager.create_session,
            req.api_key, req.secret_key, req.simulation,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return ConnectResponse(
        session_id=sess.session_id,
        simulation=sess.simulation,
        accounts=sess.account_info(),
        message="Connected" + (" (simulation)" if sess.simulation else " (LIVE)"),
    )


@router.delete("/connect/{session_id}")
async def disconnect(session_id: str):
    """Logout and discard the Shioaji session."""
    shioaji_manager.delete_session(session_id)
    return {"message": "Disconnected", "session_id": session_id}


@router.get("/quote/{ticker}")
async def get_quote(ticker: str, session_id: str):
    """
    Real-time snapshot quote for a Taiwan stock.
    Taiwan stocks only (numeric code, e.g. '2330' for TSMC).
    """
    sess = _get_session(session_id)
    try:
        quote = await asyncio.to_thread(shioaji_manager.get_quote, sess, ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return quote


@router.get("/balance")
async def get_balance(session_id: str):
    """Account cash balance."""
    sess = _get_session(session_id)
    try:
        return await asyncio.to_thread(shioaji_manager.get_balance, sess)
    except RuntimeError as e:
        _map_error(e)


@router.get("/positions")
async def get_positions(session_id: str):
    """List open stock positions with unrealised P&L."""
    sess = _get_session(session_id)
    try:
        return await asyncio.to_thread(shioaji_manager.get_positions, sess)
    except RuntimeError as e:
        _map_error(e)


@router.post("/order")
async def place_order(req: PlaceOrderRequest):
    """
    Place a stock order.
    In simulation mode this goes to Sinopac's paper-trading environment.
    """
    if req.action.upper() not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="action must be 'BUY' or 'SELL'")

    sess = _get_session(req.session_id)
    try:
        trade = await asyncio.to_thread(
            shioaji_manager.place_order,
            sess, req.ticker, req.action, req.price,
            req.quantity, req.price_type, req.order_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    mode = "simulation" if sess.simulation else "LIVE"
    logger.info(f"[trading] {mode} order placed: {req.action} {req.quantity}x{req.ticker} @{req.price}")
    return trade


@router.delete("/order/{trade_id}")
async def cancel_order(trade_id: str, session_id: str):
    """Cancel an open order by trade_id."""
    sess = _get_session(session_id)
    try:
        result = await asyncio.to_thread(shioaji_manager.cancel_order, sess, trade_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


@router.get("/orders")
async def list_orders(session_id: str):
    """List all orders placed in the current trading day."""
    sess = _get_session(session_id)
    try:
        return await asyncio.to_thread(shioaji_manager.list_orders, sess)
    except RuntimeError as e:
        _map_error(e)
