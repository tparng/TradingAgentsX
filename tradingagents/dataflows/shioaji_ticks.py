"""
Fetch intraday tick data from the Shioaji sidecar (port 21322) and aggregate
into microstructure metrics suitable for LLM consumption.

Only works when the Shioaji sidecar is running and logged in.
Volumes in Shioaji tick data are in shares (not 張/lots).
"""
import re
import httpx

SIDECAR_URL = "http://127.0.0.1:21322"
# Taiwan block-trade threshold: ≥10,000 shares (10 張) per tick
LARGE_LOT_THRESHOLD = 10_000


def _detect_exchange(symbol: str) -> str:
    """Return 'TSE' (TWSE) or 'OTC' (TPEx) for the given Taiwan symbol."""
    try:
        from tradingagents.dataflows.finmind_common import get_stock_market_type
        mtype = get_stock_market_type(symbol)
        if mtype in ("tpex", "rotc"):
            return "OTC"
    except Exception:
        pass
    return "TSE"


def _is_taiwan_symbol(symbol: str) -> bool:
    """Heuristic: Taiwan stock codes are 4–6 digit numbers (e.g. 2330, 00878)."""
    return bool(re.fullmatch(r"\d{4,6}", symbol))


def fetch_raw_ticks(symbol: str, date: str) -> dict | None:
    """
    Fetch raw tick arrays from the sidecar for *symbol* on *date*.
    Returns the sidecar JSON dict on success, None if unavailable or no data.
    """
    if not _is_taiwan_symbol(symbol):
        return None
    exchange = _detect_exchange(symbol)
    payload = {
        "contract": {"security_type": "STK", "exchange": exchange, "code": symbol},
        "date": date,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{SIDECAR_URL}/api/v1/data/ticks", json=payload)
            r.raise_for_status()
            data = r.json()
        if not data.get("close"):
            return None
        return data
    except Exception:
        return None


def get_tick_microstructure(symbol: str, date: str) -> str:
    """
    Fetch all intraday ticks for *symbol* on *date* from the Shioaji sidecar
    and compute microstructure metrics.

    Args:
        symbol: Taiwan stock code (e.g. "2330")
        date:   Trading date in YYYY-MM-DD format

    Returns:
        Markdown-formatted microstructure summary, or an error string if the
        sidecar is unavailable or no data exists for the date.
    """
    if not _is_taiwan_symbol(symbol):
        return (
            f"[tick_microstructure] {symbol} does not look like a Taiwan stock code "
            f"— tick data is only available for TWSE/TPEx stocks via the Shioaji sidecar."
        )

    exchange = _detect_exchange(symbol)
    payload = {
        "contract": {"security_type": "STK", "exchange": exchange, "code": symbol},
        "date": date,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{SIDECAR_URL}/api/v1/data/ticks", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        return (
            f"[tick_microstructure] Shioaji sidecar unavailable — skipping tick analysis. "
            f"({exc})"
        )

    closes     = data.get("close", [])
    volumes    = data.get("volume", [])
    bid_prices = data.get("bid_price", [])
    ask_prices = data.get("ask_price", [])
    tick_types = data.get("tick_type", [])  # 1=buy-initiated, 2=sell-initiated, 0=unknown

    n = len(closes)
    if n == 0:
        return f"[tick_microstructure] No tick data for {symbol} on {date} (market closed or symbol delisted)."

    # ── Aggregate metrics ─────────────────────────────────────────────────────

    total_volume = sum(volumes)

    buy_vol  = sum(v for v, t in zip(volumes, tick_types) if t == 1)
    sell_vol = sum(v for v, t in zip(volumes, tick_types) if t == 2)
    imbalance = (buy_vol - sell_vol) / total_volume if total_volume else 0.0

    vwap = (
        sum(c * v for c, v in zip(closes, volumes)) / total_volume
        if total_volume else 0.0
    )

    avg_size = total_volume / n if n else 0.0

    # Block trades
    large_lots = [(c, v) for c, v in zip(closes, volumes) if v >= LARGE_LOT_THRESHOLD]
    large_lot_count  = len(large_lots)
    large_lot_volume = sum(v for _, v in large_lots)
    large_lot_pct    = large_lot_volume / total_volume * 100 if total_volume else 0.0

    # Intraday momentum: early 10 % of session vs late 10 %
    seg = max(1, n // 10)
    early_avg = sum(closes[:seg]) / seg
    late_avg  = sum(closes[-seg:]) / seg
    momentum_pct = (late_avg - early_avg) / early_avg * 100 if early_avg else 0.0

    # Average bid-ask spread
    spreads   = [a - b for b, a in zip(bid_prices, ask_prices) if b > 0 and a > 0]
    avg_spread = sum(spreads) / len(spreads) if spreads else 0.0

    last_price    = closes[-1] if closes else 0.0
    vwap_dev      = (last_price - vwap) / vwap * 100 if vwap else 0.0

    # ── Narrative labels ──────────────────────────────────────────────────────

    if imbalance > 0.20:
        imb_label = "強買方主導 (Strong buy pressure)"
    elif imbalance > 0.05:
        imb_label = "買方略占優 (Mild buy bias)"
    elif imbalance < -0.20:
        imb_label = "強賣方主導 (Strong sell pressure)"
    elif imbalance < -0.05:
        imb_label = "賣方略占優 (Mild sell bias)"
    else:
        imb_label = "買賣均衡 (Balanced)"

    if momentum_pct > 0.5:
        mom_label = "尾盤強勁走強 (Late-session surge)"
    elif momentum_pct > 0.1:
        mom_label = "尾盤略偏強 (Late-session mild strength)"
    elif momentum_pct < -0.5:
        mom_label = "尾盤明顯走弱 (Late-session sell-off)"
    elif momentum_pct < -0.1:
        mom_label = "尾盤略偏弱 (Late-session mild weakness)"
    else:
        mom_label = "盤中走勢平穩 (Stable throughout session)"

    vwap_label = (
        "收盤守 VWAP 之上 → 多方控盤 (Closed above VWAP — bullish control)"
        if vwap_dev >= 0
        else "收盤跌破 VWAP → 空方壓制 (Closed below VWAP — bearish control)"
    )

    inst_label = (
        "法人參與度高，籌碼集中 (High institutional activity)"
        if large_lot_pct > 40
        else "散戶主導，籌碼分散 (Retail-dominated)"
    )

    # ── Format markdown table + interpretation ────────────────────────────────
    lines = [
        f"## {symbol} Intraday Microstructure — {date}  ({exchange})",
        "",
        "| Metric | Value | Interpretation |",
        "|--------|-------|----------------|",
        f"| Tick count | {n:,} | Total trades executed |",
        f"| Total volume | {total_volume:,} shares | |",
        f"| Avg trade size | {avg_size:.0f} shares/tick | Retail vs institutional proxy |",
        f"| VWAP | {vwap:.2f} TWD | Volume-weighted avg price |",
        f"| Last price | {last_price:.2f} TWD | |",
        f"| Price vs VWAP | {vwap_dev:+.2f}% | {vwap_label} |",
        f"| Buy volume | {buy_vol:,} ({buy_vol/total_volume*100:.1f}%) | Buyer-initiated trades |",
        f"| Sell volume | {sell_vol:,} ({sell_vol/total_volume*100:.1f}%) | Seller-initiated trades |",
        f"| Order flow imbalance | {imbalance:+.3f} | {imb_label} |",
        f"| Block trades (≥{LARGE_LOT_THRESHOLD:,} shares) | {large_lot_count:,} ticks ({large_lot_pct:.1f}% of volume) | {inst_label} |",
        f"| Intraday momentum | {momentum_pct:+.2f}% | {mom_label} |",
        f"| Avg bid-ask spread | {avg_spread:.2f} TWD | Liquidity indicator |",
        "",
        "### Key Signals",
        f"- **Order flow**: {imb_label} (imbalance index {imbalance:+.3f})",
        f"- **VWAP position**: {vwap_label}",
        f"- **Institutional footprint**: block trades account for {large_lot_pct:.1f}% of volume — {inst_label}",
        f"- **Session momentum**: {mom_label} ({momentum_pct:+.2f}% early→late)",
    ]

    return "\n".join(lines)
