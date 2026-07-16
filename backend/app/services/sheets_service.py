"""
Google Sheets sync service for watchlist management.
Authenticates via a GCP service account (GOOGLE_SERVICE_ACCOUNT_JSON env var).

Sheet layout (tab named "Watchlist"):
  A: Ticker  B: Market  C: Notes  D: Added At  E: Last Analyzed  F: Recommendation  G: Score
"""
import json
import logging
import asyncio
import base64
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_HEADERS = ["Ticker", "Market", "Notes", "Added At", "Last Analyzed", "Recommendation", "Score"]


class SheetsService:
    def __init__(self):
        self._client = None
        self._worksheet = None

    def is_configured(self) -> bool:
        import os
        return bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("GOOGLE_SHEET_ID"))

    def _get_client(self):
        if self._client is not None:
            return self._client
        import os
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        try:
            creds_dict = json.loads(raw)
        except json.JSONDecodeError:
            creds_dict = json.loads(base64.b64decode(raw).decode())

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        self._client = gspread.authorize(creds)
        return self._client

    def _get_worksheet(self):
        if self._worksheet is not None:
            return self._worksheet
        import os
        client = self._get_client()
        spreadsheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID", ""))
        try:
            ws = spreadsheet.worksheet("Watchlist")
        except Exception:
            ws = spreadsheet.add_worksheet(title="Watchlist", rows=1000, cols=10)
            ws.append_row(_HEADERS)

        # Ensure header row exists
        first = ws.row_values(1)
        if not first or first[0].lower() != "ticker":
            ws.insert_row(_HEADERS, 1)

        self._worksheet = ws
        return ws

    def _reset_cache(self):
        self._worksheet = None

    # ── Public async API ──────────────────────────────────────────────────────

    async def get_tickers_from_sheet(self) -> list[dict]:
        """Return all watchlist rows from the Sheet as a list of dicts."""
        if not self.is_configured():
            return []

        def _read():
            ws = self._get_worksheet()
            rows = ws.get_all_records()
            result = []
            _VALID_MARKETS = {"us", "twse", "tpex"}
            _SKIP_TICKERS = {"stock_id", "ticker", "symbol", "code", "股票代碼"}
            for row in rows:
                ticker = str(row.get("Ticker", "")).strip().upper()
                if not ticker or ticker.lower() in _SKIP_TICKERS:
                    continue

                # Column B may be market code OR legacy company name
                raw_market = str(row.get("Market", "")).strip().lower()
                if raw_market in _VALID_MARKETS:
                    market_type = raw_market
                    company = ""
                else:
                    # Auto-detect: pure digits → twse; otherwise → us
                    market_type = "twse" if ticker.isdigit() else "us"
                    company = raw_market  # treat it as company name

                # Build notes: combine company name (col B) + category (col C)
                category = str(row.get("Notes", "")).strip()
                notes_parts = [p for p in [company, category] if p]
                notes = " · ".join(notes_parts)

                result.append({
                    "ticker": ticker,
                    "market_type": market_type,
                    "notes": notes,
                })
            return result

        try:
            return await asyncio.to_thread(_read)
        except Exception as e:
            logger.error(f"Failed to read from Google Sheet: {e}")
            self._reset_cache()
            return []

    async def add_ticker_to_sheet(self, ticker: str, market_type: str, notes: str = ""):
        """Append a new row for *ticker* (no-op if already present)."""
        if not self.is_configured():
            return

        def _add():
            ws = self._get_worksheet()
            try:
                if ws.find(ticker, in_column=1):
                    return
            except Exception:
                pass
            ws.append_row([
                ticker,
                market_type,
                notes,
                datetime.utcnow().strftime("%Y-%m-%d"),
                "", "", "",
            ])

        try:
            await asyncio.to_thread(_add)
        except Exception as e:
            logger.error(f"Failed to add {ticker} to Sheet: {e}")
            self._reset_cache()

    async def remove_ticker_from_sheet(self, ticker: str):
        """Delete the row for *ticker* from the Sheet."""
        if not self.is_configured():
            return

        def _remove():
            ws = self._get_worksheet()
            try:
                cell = ws.find(ticker, in_column=1)
                if cell:
                    ws.delete_rows(cell.row)
            except Exception:
                pass

        try:
            await asyncio.to_thread(_remove)
        except Exception as e:
            logger.error(f"Failed to remove {ticker} from Sheet: {e}")
            self._reset_cache()

    async def write_analysis_result(
        self,
        ticker: str,
        recommendation: Optional[str],
        score: Optional[float],
        analyzed_at: Optional[datetime] = None,
    ):
        """Update columns E–G for the row matching *ticker*."""
        if not self.is_configured():
            return

        def _write():
            ws = self._get_worksheet()
            cell = ws.find(ticker, in_column=1)
            if cell is None:
                logger.warning(f"Ticker {ticker} not found in Sheet — skipping result write")
                return
            ts = (analyzed_at or datetime.utcnow()).strftime("%Y-%m-%d %H:%M")
            ws.update_cell(cell.row, 5, ts)
            ws.update_cell(cell.row, 6, recommendation or "")
            ws.update_cell(cell.row, 7, round(score, 1) if score is not None else "")

        try:
            await asyncio.to_thread(_write)
        except Exception as e:
            logger.error(f"Failed to write result for {ticker} to Sheet: {e}")
            self._reset_cache()


sheets_service = SheetsService()
