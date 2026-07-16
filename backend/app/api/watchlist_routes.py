"""
Watchlist CRUD + trigger routes.

GET    /api/watchlist           — list all items
POST   /api/watchlist           — add a ticker
DELETE /api/watchlist/{ticker}  — remove a ticker
POST   /api/watchlist/sync      — manual Sheet → DB sync
POST   /api/watchlist/analyze   — trigger analysis (all or specific ticker)
GET    /api/watchlist/status    — scheduler + service status
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete

from backend.app.db.database import get_db
from backend.app.db.models import WatchlistItem
from backend.app.services.sheets_service import sheets_service
from backend.app.services.telegram_service import telegram_service
from backend.app.services.scheduler_service import scheduler, sync_sheet_job, run_watchlist_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AddTickerRequest(BaseModel):
    ticker: str
    market_type: str = "us"
    notes: Optional[str] = ""


class AnalyzeTriggerRequest(BaseModel):
    ticker: Optional[str] = None  # None → analyze all


class WatchlistItemOut(BaseModel):
    id: str
    ticker: str
    market_type: str
    notes: Optional[str]
    added_at: str
    last_analyzed_at: Optional[str]
    last_recommendation: Optional[str]
    last_score: Optional[float]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WatchlistItemOut])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at))
    return [_to_out(item) for item in result.scalars().all()]


@router.post("", response_model=WatchlistItemOut, status_code=201)
async def add_to_watchlist(req: AddTickerRequest, db: AsyncSession = Depends(get_db)):
    ticker = req.ticker.strip().upper()

    existing = (await db.execute(
        select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"{ticker} is already in the watchlist")

    item = WatchlistItem(ticker=ticker, market_type=req.market_type, notes=req.notes or "")
    db.add(item)
    await db.commit()
    await db.refresh(item)

    await sheets_service.add_ticker_to_sheet(ticker, req.market_type, req.notes or "")
    return _to_out(item)


@router.delete("/{ticker}", status_code=204)
async def remove_from_watchlist(ticker: str, db: AsyncSession = Depends(get_db)):
    ticker = ticker.strip().upper()
    item = (await db.execute(
        select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"{ticker} not in watchlist")

    await db.execute(sa_delete(WatchlistItem).where(WatchlistItem.ticker == ticker))
    await db.commit()
    await sheets_service.remove_ticker_from_sheet(ticker)


@router.post("/sync", status_code=200)
async def sync_from_sheet():
    """Manually trigger a Sheet → DB sync."""
    if not sheets_service.is_configured():
        raise HTTPException(status_code=400, detail="Google Sheets not configured (missing GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SHEET_ID)")
    await sync_sheet_job()
    return {"message": "Sync complete"}


@router.post("/analyze", status_code=202)
async def trigger_analysis(req: AnalyzeTriggerRequest = AnalyzeTriggerRequest()):
    """
    Fire watchlist analysis in the background.
    Pass {"ticker": "AAPL"} to analyze a single ticker, or an empty body for all.
    """
    tickers = [req.ticker.strip().upper()] if req.ticker else None

    async def _run():
        await run_watchlist_analysis(tickers)

    asyncio.create_task(_run())
    scope = tickers[0] if tickers else "all watchlist tickers"
    return {"message": f"Analysis started for {scope}"}


@router.get("/status")
async def scheduler_status():
    return {
        "jobs": scheduler.get_jobs(),
        "sheets_configured": sheets_service.is_configured(),
        "telegram_configured": telegram_service.is_configured(),
    }


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_out(item: WatchlistItem) -> WatchlistItemOut:
    return WatchlistItemOut(
        id=str(item.id),
        ticker=item.ticker,
        market_type=item.market_type,
        notes=item.notes,
        added_at=item.added_at.isoformat(),
        last_analyzed_at=item.last_analyzed_at.isoformat() if item.last_analyzed_at else None,
        last_recommendation=item.last_recommendation,
        last_score=item.last_score,
    )
