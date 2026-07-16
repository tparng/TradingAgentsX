"""
APScheduler-based scheduler for:
  1. Sheet sync   — every 15 minutes: pulls watchlist from Google Sheet into DB
  2. Daily analysis — cron from WATCHLIST_ANALYSIS_CRON: runs all watchlist tickers
"""
import os
import logging
import asyncio
from datetime import datetime, date
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class WatchlistScheduler:
    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start(self):
        self._scheduler = AsyncIOScheduler()

        self._scheduler.add_job(
            sync_sheet_job,
            trigger=IntervalTrigger(minutes=15),
            id="sheet_sync",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=60,
        )

        cron_expr = os.getenv("WATCHLIST_ANALYSIS_CRON", "").strip()
        if cron_expr:
            parts = cron_expr.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                self._scheduler.add_job(
                    daily_analysis_job,
                    trigger=CronTrigger(
                        minute=minute, hour=hour,
                        day=day, month=month, day_of_week=day_of_week,
                    ),
                    id="daily_analysis",
                    replace_existing=True,
                    max_instances=1,
                    misfire_grace_time=3600,
                )
                logger.info(f"Daily watchlist analysis scheduled: {cron_expr}")
            else:
                logger.warning(f"Invalid WATCHLIST_ANALYSIS_CRON: {cron_expr!r} — must be 5 fields")
        else:
            logger.info("WATCHLIST_ANALYSIS_CRON not set — scheduled auto-analysis disabled")

        self._scheduler.start()
        logger.info("Watchlist scheduler started")

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Watchlist scheduler stopped")

    def get_jobs(self) -> list[dict]:
        if not self._scheduler:
            return []
        return [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in self._scheduler.get_jobs()
        ]


# ── Scheduler jobs ─────────────────────────────────────────────────────────────

async def sync_sheet_job():
    """Pull watchlist rows from Google Sheet and reconcile with DB."""
    from backend.app.services.sheets_service import sheets_service
    from backend.app.db.database import AsyncSessionLocal
    from backend.app.db.models import WatchlistItem
    from sqlalchemy import select, delete as sa_delete

    if not sheets_service.is_configured() or AsyncSessionLocal is None:
        return

    logger.info("Sheet sync: starting")
    try:
        sheet_items = await sheets_service.get_tickers_from_sheet()
        sheet_map = {item["ticker"]: item for item in sheet_items}

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(WatchlistItem))
            db_map = {item.ticker: item for item in result.scalars().all()}

            # Add tickers present in Sheet but not in DB
            for ticker, info in sheet_map.items():
                if ticker not in db_map:
                    session.add(WatchlistItem(
                        ticker=ticker,
                        market_type=info.get("market_type", "us"),
                        notes=info.get("notes", ""),
                    ))
                    logger.info(f"Sheet sync: added {ticker}")

            # Remove tickers in DB that were deleted from Sheet
            for ticker in list(db_map.keys()):
                if ticker not in sheet_map:
                    await session.execute(sa_delete(WatchlistItem).where(WatchlistItem.ticker == ticker))
                    logger.info(f"Sheet sync: removed {ticker}")

            await session.commit()
        logger.info(f"Sheet sync: done ({len(sheet_map)} tickers)")
    except Exception as e:
        logger.error(f"Sheet sync job failed: {e}", exc_info=True)


async def daily_analysis_job():
    """Analyze all watchlist tickers; write results to Sheet + Telegram."""
    await run_watchlist_analysis()


async def run_watchlist_analysis(tickers: Optional[list[str]] = None):
    """
    Run analysis for *tickers* (or all watchlist items when None).
    Uses server-side LLM config from env vars (WATCHLIST_* prefix).
    """
    from backend.app.db.database import AsyncSessionLocal
    from backend.app.db.models import WatchlistItem
    from backend.app.services.sheets_service import sheets_service
    from backend.app.services.telegram_service import telegram_service
    from backend.app.services.trading_service import TradingService
    from sqlalchemy import select

    if AsyncSessionLocal is None:
        logger.warning("run_watchlist_analysis: DB not configured")
        return

    today = date.today().strftime("%Y-%m-%d")
    async with AsyncSessionLocal() as session:
        q = select(WatchlistItem)
        if tickers:
            q = q.where(WatchlistItem.ticker.in_([t.upper() for t in tickers]))
        result = await session.execute(q)
        items = result.scalars().all()

    if not items:
        logger.info("run_watchlist_analysis: no matching items")
        return

    deep_llm = os.getenv("WATCHLIST_DEEP_THINK_LLM", "qwen2.5:14b")
    quick_llm = os.getenv("WATCHLIST_QUICK_THINK_LLM", "qwen2.5:14b")
    deep_url = os.getenv("WATCHLIST_DEEP_THINK_BASE_URL", "http://localhost:11434/v1")
    quick_url = os.getenv("WATCHLIST_QUICK_THINK_BASE_URL", "http://localhost:11434/v1")
    deep_key = os.getenv("WATCHLIST_DEEP_THINK_API_KEY", "ollama")
    quick_key = os.getenv("WATCHLIST_QUICK_THINK_API_KEY", "ollama")
    analysts = [a.strip() for a in os.getenv("WATCHLIST_ANALYSTS", "market,fundamentals,quant").split(",") if a.strip()]
    language = os.getenv("WATCHLIST_REPORT_LANGUAGE", "zh-TW")

    service = TradingService()

    for item in items:
        logger.info(f"Analyzing watchlist item: {item.ticker}")
        try:
            result = await asyncio.to_thread(
                _run_analysis_sync, service,
                item.ticker, today,
                deep_llm, quick_llm, deep_url, quick_url,
                deep_key, quick_key, analysts, item.market_type, language,
            )

            if result.get("status") == "success":
                decision = result.get("decision") or {}
                recommendation = decision.get("action") or decision.get("decision")
                score = decision.get("confidence")
                if isinstance(score, (int, float)):
                    score = float(score) * 100 if score <= 1.0 else float(score)

                async with AsyncSessionLocal() as session:
                    db_item = await session.get(WatchlistItem, item.id)
                    if db_item:
                        db_item.last_analyzed_at = datetime.utcnow()
                        db_item.last_recommendation = recommendation
                        db_item.last_score = score
                        await session.commit()

                await sheets_service.write_analysis_result(
                    item.ticker, recommendation, score, datetime.utcnow()
                )
                await telegram_service.send_analysis_complete(
                    item.ticker, item.market_type, recommendation, score, today
                )
                logger.info(f"{item.ticker}: done — {recommendation}")
            else:
                error = result.get("error", "unknown error")
                logger.error(f"{item.ticker}: analysis failed — {error}")
                await telegram_service.send_error(item.ticker, error)

        except Exception as e:
            logger.error(f"{item.ticker}: exception — {e}", exc_info=True)
            await telegram_service.send_error(item.ticker, str(e))

    logger.info("run_watchlist_analysis: complete")


def _run_analysis_sync(
    service, ticker, analysis_date,
    deep_think_llm, quick_think_llm,
    deep_base_url, quick_base_url,
    deep_api_key, quick_api_key,
    analysts, market_type, language,
):
    """Wrap the async analysis coroutine for use in asyncio.to_thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(service.run_analysis(
            ticker=ticker,
            analysis_date=analysis_date,
            deep_think_llm=deep_think_llm,
            quick_think_llm=quick_think_llm,
            deep_think_base_url=deep_base_url,
            quick_think_base_url=quick_base_url,
            deep_think_api_key=deep_api_key,
            quick_think_api_key=quick_api_key,
            analysts=analysts,
            market_type=market_type,
            language=language,
        ))
    finally:
        loop.close()


scheduler = WatchlistScheduler()
