"""
LangChain tool wrappers around stock-strategies-only's quantitative evaluation functions.
stock_strategies is imported via sys.path since it's not a pip-installable package.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Add stock-strategies-only to path if not already importable
# parents[3] = TradingAgentsX repo root; sibling dir is ../stock-strategies-only
_SSO_PATH = str((Path(__file__).parents[3] / "../stock-strategies-only").resolve())
if _SSO_PATH not in sys.path:
    sys.path.insert(0, _SSO_PATH)

try:
    from stock_strategies.evaluate import evaluate
    from stock_strategies.loader import get_strategy
    from stock_strategies.data import is_us_stock
    from stock_strategies.datasources import get_institutional, get_month_revenue, get_valuation
    _HAS_STOCK_STRATEGIES = True
except ImportError:
    _HAS_STOCK_STRATEGIES = False


def _set_finmind_token():
    """Propagate FinMind token from TradingAgentsX env vars to FINMIND_TOKEN."""
    if os.environ.get("FINMIND_TOKEN"):
        return
    for var in ("FINMIND_API_TOKEN", "FINMIND_API_KEY"):
        val = os.environ.get(var, "")
        if val:
            os.environ["FINMIND_TOKEN"] = val
            return


# ---------------------------------------------------------------------------
# 1. get_quant_evaluation  (primary quant analyst tool)
# ---------------------------------------------------------------------------

class GetQuantEvaluationInput(BaseModel):
    ticker: str = Field(description="Stock ticker (e.g. 'NVDA' for US, '2330' for TSMC)")
    curr_date: str = Field(description="Analysis date in YYYY-MM-DD format")


def _get_quant_evaluation(ticker: str, curr_date: str) -> str:
    if not _HAS_STOCK_STRATEGIES:
        return "Quant evaluation unavailable: stock-strategies-only not found at ../stock-strategies-only."

    _set_finmind_token()

    try:
        strategy = get_strategy("default")
    except Exception:
        strategy = {}

    try:
        result = evaluate(ticker, ticker, strategy)
    except Exception as e:
        return f"Quant evaluation failed for {ticker}: {e}"

    comp = result.get("components") or {}
    trend = result.get("trend") or {}

    lines = [
        f"=== Quantitative Evaluation: {ticker} (as of {curr_date}) ===",
        f"Signal:          {result.get('action', 'N/A')}",
        f"Composite Score: {result.get('signal_score', 0):.1f} / 100",
        "",
        "Fundamental:",
    ]

    # US path
    if "us_fund_score" in comp:
        lines.append(f"  US Fund Score:  {comp['us_fund_score']:.1f} / 100")
        for sig in (comp.get("us_fund_signals") or []):
            lines.append(f"    + {sig}")
    # TW path
    elif "fund_score" in comp:
        lines.append(f"  Fund Score:     {comp['fund_score']:.1f} / 100")

    lines += ["", "Technical:"]
    if "tech_score" in comp:
        lines.append(f"  Tech Score:     {comp['tech_score']} / 100")
    for sig in (comp.get("tech_signals") or []):
        lines.append(f"    + {sig}")

    lines += ["", "Backtest (3-year):"]
    if "backtest_winrate" in comp:
        wr = comp["backtest_winrate"]
        n  = comp.get("backtest_samples", "?")
        lines.append(f"  Win Rate:       {wr*100:.1f}%  ({n} samples)")

    entry  = result.get("entry_price", "N/A")
    stop   = result.get("stop_loss_price", "N/A")
    target = result.get("target_price", "N/A")
    rr     = result.get("risk_reward_ratio", "N/A")
    pos    = result.get("position_size_pct", result.get("position_size", "N/A"))
    lines += [
        "",
        "Trade Setup:",
        f"  Entry Price:    {entry:.2f}" if isinstance(entry, float) else f"  Entry Price:    {entry}",
        f"  Stop Loss:      {stop:.2f}"  if isinstance(stop,  float) else f"  Stop Loss:      {stop}",
        f"  Target Price:   {target:.2f}" if isinstance(target, float) else f"  Target Price:   {target}",
        f"  Risk/Reward:    {rr}",
        f"  Position Size:  {pos}%"      if isinstance(pos,   float) else f"  Position Size:  {pos}",
    ]

    if trend:
        lines += [
            "",
            "Price Trend:",
            f"  5-day return:   {trend.get('chg_5d', 'N/A'):.2f}%" if isinstance(trend.get('chg_5d'), float) else "",
            f"  20-day return:  {trend.get('chg_20d', 'N/A'):.2f}%" if isinstance(trend.get('chg_20d'), float) else "",
            f"  Above MA20:     {trend.get('above_ma20', 'N/A')}",
            f"  Above MA60:     {trend.get('above_ma60', 'N/A')}",
            f"  From 52w-high:  {trend.get('pct_from_high', 'N/A'):.1f}%" if isinstance(trend.get('pct_from_high'), float) else "",
        ]
        lines = [l for l in lines if l]  # remove blank entries

    vol_verdict = comp.get("volume_verdict", "")
    if vol_verdict:
        lines += ["", f"Volume Pattern: {vol_verdict}"]

    for pat in (comp.get("volume_patterns") or []):
        lines.append(f"  + {pat}")

    risk_notes = result.get("risk_notes") or []
    if risk_notes:
        lines += ["", "Risk Notes:"]
        for n in risk_notes:
            lines.append(f"  ! {n}")

    return "\n".join(lines)


get_quant_evaluation = StructuredTool.from_function(
    func=_get_quant_evaluation,
    name="get_quant_evaluation",
    description=(
        "Run a full quantitative evaluation of a stock using the stock-strategies scoring engine. "
        "Returns a composite score (0-100), sub-scores for fundamental/technical/backtest components, "
        "a BUY/WATCH/SKIP signal, entry/stop-loss/target prices, suggested position size, "
        "technical signals, volume patterns, and risk notes. "
        "Works for both US tickers (e.g. 'NVDA') and Taiwan tickers (e.g. '2330'). "
        "Note: price data is fetched from current market, not point-in-time historical."
    ),
    args_schema=GetQuantEvaluationInput,
)


# ---------------------------------------------------------------------------
# 2. get_institutional_flows  (Taiwan-only chips data)
# ---------------------------------------------------------------------------

class GetInstitutionalFlowsInput(BaseModel):
    ticker: str = Field(description="Taiwan stock ticker (numeric, e.g. '2330')")
    curr_date: str = Field(description="End date in YYYY-MM-DD format")


def _get_institutional_flows(ticker: str, curr_date: str) -> str:
    if not _HAS_STOCK_STRATEGIES:
        return "Institutional flows unavailable: stock-strategies-only not found."

    _set_finmind_token()

    if is_us_stock(ticker):
        return f"Institutional flow data (3-major-investors) is Taiwan-only; {ticker} is a US ticker."

    try:
        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start  = (end_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        df = get_institutional(ticker, start)
        if df is None or df.empty:
            return f"No institutional flow data for {ticker}."
        df = df[df.index <= curr_date].tail(30)
        return f"3-Major-Investor Net Buy/Sell for {ticker} (past 30 trading days):\n{df.to_string()}"
    except Exception as e:
        return f"Failed to fetch institutional flows for {ticker}: {e}"


get_institutional_flows = StructuredTool.from_function(
    func=_get_institutional_flows,
    name="get_institutional_flows",
    description=(
        "Get 3-major-investor (foreign/trust/dealer) daily net buy/sell flow data for a Taiwan stock "
        "over the past 30 trading days. Columns: foreign_net, trust_net, dealer_net, total_net. "
        "Taiwan stocks only (numeric ticker like '2330')."
    ),
    args_schema=GetInstitutionalFlowsInput,
)


# ---------------------------------------------------------------------------
# 3. get_revenue_trend  (Taiwan-only monthly revenue)
# ---------------------------------------------------------------------------

class GetRevenueTrendInput(BaseModel):
    ticker: str = Field(description="Taiwan stock ticker (numeric, e.g. '2330')")
    curr_date: str = Field(description="End date in YYYY-MM-DD format")


def _get_revenue_trend(ticker: str, curr_date: str) -> str:
    if not _HAS_STOCK_STRATEGIES:
        return "Revenue trend unavailable: stock-strategies-only not found."

    _set_finmind_token()

    if is_us_stock(ticker):
        return f"Monthly revenue data from FinMind is Taiwan-only; {ticker} is a US ticker."

    try:
        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start  = (end_dt - timedelta(days=400)).strftime("%Y-%m-%d")
        df = get_month_revenue(ticker, start)
        if df is None or df.empty:
            return f"No revenue data for {ticker}."
        df = df[df["avail_date"] <= curr_date].tail(12)
        cols = [c for c in ("revenue", "mom", "yoy") if c in df.columns]
        return f"Monthly Revenue Trend for {ticker} (last 12 months):\n{df[cols].to_string()}"
    except Exception as e:
        return f"Failed to fetch revenue trend for {ticker}: {e}"


get_revenue_trend = StructuredTool.from_function(
    func=_get_revenue_trend,
    name="get_revenue_trend",
    description=(
        "Get monthly revenue data for a Taiwan stock including MoM and YoY growth rates "
        "for the past 12 months, with look-ahead bias prevention (uses avail_date). "
        "Taiwan stocks only (numeric ticker like '2330')."
    ),
    args_schema=GetRevenueTrendInput,
)


# ---------------------------------------------------------------------------
# 4. get_valuation_metrics  (Taiwan-only PER/PBR/yield)
# ---------------------------------------------------------------------------

class GetValuationMetricsInput(BaseModel):
    ticker: str = Field(description="Taiwan stock ticker (numeric, e.g. '2330')")
    curr_date: str = Field(description="End date in YYYY-MM-DD format")


def _get_valuation_metrics(ticker: str, curr_date: str) -> str:
    if not _HAS_STOCK_STRATEGIES:
        return "Valuation metrics unavailable: stock-strategies-only not found."

    _set_finmind_token()

    if is_us_stock(ticker):
        return f"Daily PER/PBR/yield from FinMind is Taiwan-only; {ticker} is a US ticker."

    try:
        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start  = (end_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        df = get_valuation(ticker, start)
        if df is None or df.empty:
            return f"No valuation data for {ticker}."
        df = df[df.index <= curr_date].tail(30)
        return f"Valuation Metrics (PER / PBR / Dividend Yield) for {ticker}:\n{df.to_string()}"
    except Exception as e:
        return f"Failed to fetch valuation metrics for {ticker}: {e}"


get_valuation_metrics = StructuredTool.from_function(
    func=_get_valuation_metrics,
    name="get_valuation_metrics",
    description=(
        "Get daily P/E ratio (PER), P/B ratio (PBR), and dividend yield for a Taiwan stock "
        "over the past 30 days. Taiwan stocks only (numeric ticker like '2330')."
    ),
    args_schema=GetValuationMetricsInput,
)
