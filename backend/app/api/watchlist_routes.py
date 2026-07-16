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
from backend.app.db.models import WatchlistItem, WatchlistCandidate
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


class CandidateOut(BaseModel):
    id: str
    ticker: str
    market_type: str
    price_change_pct: Optional[float]
    volume_ratio: Optional[float]
    rsi: Optional[float]
    rationale: Optional[str]
    rank: Optional[int]
    signal: Optional[str]
    screened_at: str
    status: str


class BulkAddRequest(BaseModel):
    tickers: list[str]


class ScreenerParams(BaseModel):
    min_price_change_pct: float = 1.5   # minimum |1-day price change %| to pass filter
    min_volume_ratio: float = 1.5       # minimum volume/20d-avg ratio to pass filter
    price_change_weight: float = 0.6    # scoring weight for price change (volume = 1 - this)
    include_us: bool = True
    include_tw: bool = True
    max_screener_candidates: int = 20   # top-N passed from screener to LLM
    llm_top_n: int = 8                  # top-N the LLM returns


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


# ── Candidate routes ──────────────────────────────────────────────────────────

@router.post("/candidates/generate", response_model=list[CandidateOut])
async def generate_candidates(
    params: ScreenerParams = ScreenerParams(),
    db: AsyncSession = Depends(get_db),
):
    """Run screener + LLM ranking with configurable parameters. Replaces all pending candidates."""
    import os
    from backend.app.services.screener_service import run_screener
    from backend.app.services.candidate_service import rank_candidates

    screened = await run_screener(
        min_price_change_pct=params.min_price_change_pct,
        min_volume_ratio=params.min_volume_ratio,
        price_change_weight=params.price_change_weight,
        include_us=params.include_us,
        include_tw=params.include_tw,
        max_candidates=params.max_screener_candidates,
    )
    if not screened:
        return []

    language = os.getenv("WATCHLIST_REPORT_LANGUAGE", "zh-TW")
    ranked = await rank_candidates(screened, language=language, top_n=params.llm_top_n)

    screened_map = {c["ticker"]: c for c in screened}

    # Clear the entire candidates table before inserting the fresh batch
    await db.execute(sa_delete(WatchlistCandidate))

    now = datetime.utcnow()
    saved = []
    for r in ranked:
        ticker = r["ticker"]
        sc = screened_map.get(ticker, {})
        candidate = WatchlistCandidate(
            ticker=ticker,
            market_type=sc.get("market_type", "us"),
            price_change_pct=sc.get("price_change_pct"),
            volume_ratio=sc.get("volume_ratio"),
            rsi=sc.get("rsi"),
            rationale=r.get("rationale", ""),
            rank=r.get("rank"),
            signal=r.get("signal", "NEUTRAL"),
            screened_at=now,
            status="pending",
        )
        db.add(candidate)
        saved.append(candidate)

    await db.commit()
    for c in saved:
        await db.refresh(c)
    return [_candidate_to_out(c) for c in saved]


@router.get("/candidates", response_model=list[CandidateOut])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistCandidate)
        .where(WatchlistCandidate.status == "pending")
        .order_by(WatchlistCandidate.rank)
    )
    return [_candidate_to_out(c) for c in result.scalars().all()]


@router.post("/candidates/add", status_code=200)
async def add_candidates_to_watchlist(req: BulkAddRequest, db: AsyncSession = Depends(get_db)):
    """Bulk-add selected candidates to the watchlist."""
    added, skipped = [], []
    for raw_ticker in req.tickers:
        ticker = raw_ticker.strip().upper()

        candidate = (await db.execute(
            select(WatchlistCandidate).where(WatchlistCandidate.ticker == ticker)
        )).scalar_one_or_none()

        existing = (await db.execute(
            select(WatchlistItem).where(WatchlistItem.ticker == ticker)
        )).scalar_one_or_none()

        if existing:
            skipped.append(ticker)
        else:
            market_type = candidate.market_type if candidate else "us"
            db.add(WatchlistItem(ticker=ticker, market_type=market_type, notes=""))
            added.append(ticker)
            await sheets_service.add_ticker_to_sheet(ticker, market_type, "")

        if candidate:
            candidate.status = "added"

    await db.commit()
    return {"added": added, "skipped": skipped}


@router.get("/candidates/{ticker}/detail")
async def get_candidate_detail(ticker: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch recent price data + generate a detailed LLM analysis report for a candidate.
    Called when the user clicks a candidate card. Takes ~15-40s with Ollama.
    """
    import os
    from backend.app.services.screener_service import get_ticker_detail
    from backend.app.services.candidate_service import generate_detail_report

    ticker = ticker.strip().upper()

    # Load candidate metadata from DB (for signal/rationale already stored)
    candidate_row = (await db.execute(
        select(WatchlistCandidate).where(WatchlistCandidate.ticker == ticker)
    )).scalar_one_or_none()

    candidate_data = {}
    if candidate_row:
        candidate_data = {
            "signal": candidate_row.signal,
            "rationale": candidate_row.rationale,
            "price_change_pct": candidate_row.price_change_pct,
            "volume_ratio": candidate_row.volume_ratio,
            "rsi": candidate_row.rsi,
        }
    market_type = candidate_row.market_type if candidate_row else "us"

    # Fetch fresh price data (threaded — yfinance is sync)
    ticker_detail = await asyncio.to_thread(get_ticker_detail, ticker, market_type)

    language = os.getenv("WATCHLIST_REPORT_LANGUAGE", "zh-TW")
    report_md = await generate_detail_report(
        ticker=ticker,
        market_type=market_type,
        candidate=candidate_data,
        ticker_detail=ticker_detail,
        language=language,
    )

    return {
        "ticker": ticker,
        "market_type": market_type,
        "signal": candidate_data.get("signal"),
        "price_change_pct": ticker_detail.get("price_change_pct") or candidate_data.get("price_change_pct"),
        "volume_ratio": ticker_detail.get("volume_ratio") or candidate_data.get("volume_ratio"),
        "rsi": ticker_detail.get("rsi") or candidate_data.get("rsi"),
        "current_price": ticker_detail.get("current_price"),
        "price_low_30d": ticker_detail.get("price_low_30d"),
        "price_high_30d": ticker_detail.get("price_high_30d"),
        "report_md": report_md,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.delete("/candidates/{ticker}", status_code=204)
async def dismiss_candidate(ticker: str, db: AsyncSession = Depends(get_db)):
    """Dismiss a candidate (hide from the UI)."""
    ticker = ticker.strip().upper()
    candidate = (await db.execute(
        select(WatchlistCandidate).where(WatchlistCandidate.ticker == ticker)
    )).scalar_one_or_none()
    if candidate:
        candidate.status = "dismissed"
        await db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _candidate_to_out(c: WatchlistCandidate) -> CandidateOut:
    return CandidateOut(
        id=str(c.id),
        ticker=c.ticker,
        market_type=c.market_type,
        price_change_pct=c.price_change_pct,
        volume_ratio=c.volume_ratio,
        rsi=c.rsi,
        rationale=c.rationale,
        rank=c.rank,
        signal=c.signal,
        screened_at=c.screened_at.isoformat(),
        status=c.status,
    )
