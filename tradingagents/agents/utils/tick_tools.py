from langchain_core.tools import tool
from typing import Annotated


@tool
def get_tick_microstructure(
    symbol: Annotated[str, "Taiwan stock code (e.g. 2330, 0050)"],
    date: Annotated[str, "Trading date in YYYY-MM-DD format"],
) -> str:
    """
    Fetch intraday tick data for a Taiwan stock from the Shioaji sidecar and
    return aggregated microstructure metrics: order flow imbalance, VWAP
    deviation, block-trade footprint, bid-ask spread, and session momentum.

    Only works for TWSE/TPEx stocks (4–6 digit numeric codes) when the
    Shioaji sidecar is running. Returns a descriptive error string otherwise.
    """
    from tradingagents.dataflows.shioaji_ticks import get_tick_microstructure as _impl
    return _impl(symbol, date)
