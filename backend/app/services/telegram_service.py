"""
Telegram notification service — posts messages via the Bot API using httpx.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.
"""
import os
import logging
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_REC_EMOJI = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}


class TelegramService:
    def is_configured(self) -> bool:
        return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))

    async def send_message(self, text: str) -> bool:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                })
            if resp.status_code != 200:
                logger.warning(f"Telegram API returned {resp.status_code}: {resp.text[:200]}")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_analysis_complete(
        self,
        ticker: str,
        market_type: str,
        recommendation: Optional[str],
        score: Optional[float],
        analysis_date: str,
    ):
        rec = (recommendation or "").upper()
        emoji = _REC_EMOJI.get(rec, "⚪")
        score_str = f"{score:.1f}/100" if score is not None else "N/A"
        text = (
            f"<b>📊 Watchlist Analysis Complete</b>\n"
            f"Ticker: <b>{ticker}</b> ({market_type.upper()})\n"
            f"Date: {analysis_date}\n"
            f"Decision: {emoji} <b>{rec or 'N/A'}</b>\n"
            f"Score: {score_str}"
        )
        await self.send_message(text)

    async def send_daily_digest(self, items: list[dict]):
        if not items:
            return
        today = datetime.utcnow().strftime("%Y-%m-%d")
        lines = [f"<b>📋 Watchlist Daily Digest — {today}</b>", ""]
        for item in items:
            rec = (item.get("last_recommendation") or "—").upper()
            emoji = _REC_EMOJI.get(rec, "⚪")
            score = item.get("last_score")
            score_str = f"{score:.0f}" if score is not None else "—"
            lines.append(
                f"{emoji} <b>{item['ticker']}</b> ({item['market_type'].upper()}) "
                f"— {rec} [{score_str}]"
            )
        await self.send_message("\n".join(lines))

    async def send_error(self, ticker: str, error: str):
        text = (
            f"<b>❌ Watchlist Analysis Failed</b>\n"
            f"Ticker: <b>{ticker}</b>\n"
            f"Error: {error[:300]}"
        )
        await self.send_message(text)


telegram_service = TelegramService()
