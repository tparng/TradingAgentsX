"""
Market screener: pulls US and TW stock universes via yfinance,
filters by price-change and volume anomalies, returns top candidates.
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Stock universes ────────────────────────────────────────────────────────────

US_UNIVERSE = [
    # Semiconductors / Hardware
    "NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "MU", "AMAT", "LRCX", "KLAC",
    "ASML", "TSM", "ARM", "SMCI", "MRVL",
    # Mega-cap Tech
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "NFLX", "UBER", "PLTR",
    "CRM", "ADBE", "ORCL", "NOW", "SNOW",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL", "BLK",
    # Healthcare / Biotech
    "LLY", "MRK", "PFE", "ABBV", "AMGN", "GILD", "MRNA",
    # Consumer / Retail
    "WMT", "COST", "NKE", "SBUX", "MCD", "KO", "PEP",
    # Energy / Industrial
    "XOM", "CVX", "COP", "CAT", "HON", "GE",
]

TW_UNIVERSE = [
    # TWSE blue chips
    "2330", "2317", "2454", "2382", "2308", "2303", "2882", "2881",
    "2412", "3711", "2891", "2886", "2884", "2880", "2379", "2395",
    "3008", "2345", "4938", "3034", "2049", "6505", "1301", "1303",
    "2207", "2002", "1216", "2357", "3231", "6669", "3045", "2376",
]


# ── Core screening logic ───────────────────────────────────────────────────────

def _calc_rsi(closes, period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    rsi_series = 100 - 100 / (1 + rs)
    val = rsi_series.iloc[-1]
    if val != val:  # NaN
        return None
    return round(float(val), 1)


def _score_ticker(
    ticker: str,
    market_type: str,
    close,
    volume,
    min_price_change_pct: float = 1.5,
    min_volume_ratio: float = 1.5,
    price_change_weight: float = 0.6,
) -> Optional[dict]:
    if len(close) < 5 or len(volume) < 5:
        return None

    price_change_pct = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
    lookback = volume.iloc[-21:-1] if len(volume) > 21 else volume.iloc[:-1]
    avg_vol = lookback.mean()
    vol_ratio = float(volume.iloc[-1] / avg_vol) if avg_vol > 0 else 1.0
    rsi = _calc_rsi(close)

    if abs(price_change_pct) < min_price_change_pct and vol_ratio < min_volume_ratio:
        return None

    vol_weight = 1.0 - price_change_weight
    score = abs(price_change_pct) * price_change_weight + max(0.0, vol_ratio - 1.0) * vol_weight
    return {
        "ticker": ticker,
        "market_type": market_type,
        "price_change_pct": round(price_change_pct, 2),
        "volume_ratio": round(vol_ratio, 2),
        "rsi": rsi,
        "score": round(score, 3),
    }


def _screen_universe(
    tickers: list[str],
    market: str,
    min_price_change_pct: float = 1.5,
    min_volume_ratio: float = 1.5,
    price_change_weight: float = 0.6,
) -> list[dict]:
    import yfinance as yf
    import pandas as pd

    suffix = ".TW" if market == "tw" else ""
    yf_tickers = [f"{t}{suffix}" for t in tickers]
    original_map = dict(zip(yf_tickers, tickers))
    market_type = "twse" if market == "tw" else "us"

    try:
        raw = yf.download(
            yf_tickers,
            period="30d",
            interval="1d",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"yfinance download failed ({market}): {e}")
        return []

    results = []

    if isinstance(raw.columns, pd.MultiIndex):
        available = raw.columns.get_level_values(1).unique()
        for yf_tick in yf_tickers:
            if yf_tick not in available:
                continue
            try:
                td = raw.xs(yf_tick, axis=1, level=1)
                close = td["Close"].dropna()
                volume = td["Volume"].dropna()
                candidate = _score_ticker(
                    original_map[yf_tick], market_type, close, volume,
                    min_price_change_pct, min_volume_ratio, price_change_weight,
                )
                if candidate:
                    results.append(candidate)
            except Exception:
                pass
    elif len(yf_tickers) == 1:
        try:
            close = raw["Close"].dropna()
            volume = raw["Volume"].dropna()
            candidate = _score_ticker(
                tickers[0], market_type, close, volume,
                min_price_change_pct, min_volume_ratio, price_change_weight,
            )
            if candidate:
                results.append(candidate)
        except Exception:
            pass

    return results


# ── Public async API ───────────────────────────────────────────────────────────

def get_ticker_detail(ticker: str, market_type: str) -> dict:
    """
    Fetch recent 30-day price data for a single ticker and return
    current price, 30d range, vol ratio, RSI, and last-10-day OHLCV rows.
    """
    import yfinance as yf

    suffix = ".TW" if market_type in ("twse", "tpex") else ""
    yf_tick = f"{ticker}{suffix}"

    try:
        raw = yf.download(yf_tick, period="30d", interval="1d", auto_adjust=True, progress=False)
    except Exception as e:
        logger.error(f"yfinance detail fetch failed for {yf_tick}: {e}")
        return {}

    if raw.empty:
        return {}

    # Flatten MultiIndex if present (happens with yfinance ≥0.2.x single ticker)
    if isinstance(raw.columns, __import__("pandas").MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    close = raw["Close"].dropna()
    volume = raw["Volume"].dropna()
    high_col = raw["High"].dropna()
    low_col = raw["Low"].dropna()

    if len(close) < 2:
        return {}

    price_change_pct = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
    lookback = volume.iloc[-21:-1] if len(volume) > 21 else volume.iloc[:-1]
    avg_vol = lookback.mean()
    vol_ratio = float(volume.iloc[-1] / avg_vol) if avg_vol > 0 else 1.0
    rsi = _calc_rsi(close)

    # Last 10 days of price rows
    n = min(10, len(close))
    recent_prices = []
    for i in range(len(close) - n, len(close)):
        recent_prices.append({
            "date": close.index[i].strftime("%Y-%m-%d"),
            "close": round(float(close.iloc[i]), 2),
            "high": round(float(high_col.iloc[i]), 2) if i < len(high_col) else None,
            "low": round(float(low_col.iloc[i]), 2) if i < len(low_col) else None,
            "volume": int(volume.iloc[i]) if i < len(volume) else 0,
        })

    return {
        "current_price": round(float(close.iloc[-1]), 2),
        "price_low_30d": round(float(close.min()), 2),
        "price_high_30d": round(float(close.max()), 2),
        "price_change_pct": round(price_change_pct, 2),
        "volume_ratio": round(vol_ratio, 2),
        "rsi": rsi,
        "recent_prices": recent_prices,
    }


async def run_screener(
    min_price_change_pct: float = 1.5,
    min_volume_ratio: float = 1.5,
    price_change_weight: float = 0.6,
    include_us: bool = True,
    include_tw: bool = True,
    max_candidates: int = 20,
) -> list[dict]:
    """
    Screen US and/or TW universes concurrently.
    Returns up to *max_candidates* sorted by composite score (highest first).
    """
    logger.info(
        f"Screener: starting (min_chg={min_price_change_pct}%, "
        f"min_vol={min_volume_ratio}×, wt_price={price_change_weight:.1f}, "
        f"us={include_us}, tw={include_tw}, top={max_candidates})"
    )

    kwargs = dict(
        min_price_change_pct=min_price_change_pct,
        min_volume_ratio=min_volume_ratio,
        price_change_weight=price_change_weight,
    )

    tasks = []
    if include_us:
        tasks.append(asyncio.to_thread(_screen_universe, US_UNIVERSE, "us", **kwargs))
    if include_tw:
        tasks.append(asyncio.to_thread(_screen_universe, TW_UNIVERSE, "tw", **kwargs))

    results = await asyncio.gather(*tasks)
    us_results = results[0] if include_us else []
    tw_results = results[1] if (include_us and include_tw) else (results[0] if include_tw else [])

    combined = us_results + tw_results
    combined.sort(key=lambda x: x["score"], reverse=True)
    top = combined[:max_candidates]

    logger.info(
        f"Screener: {len(top)} candidates selected "
        f"(US passed: {len(us_results)}, TW passed: {len(tw_results)})"
    )
    return top
