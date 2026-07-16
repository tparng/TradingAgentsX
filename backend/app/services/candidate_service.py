"""
LLM ranking layer for watchlist candidates.
Takes screened candidates (price/volume anomalies) and produces a
ranked, annotated shortlist with buy/sell signal and rationale.
"""
import json
import logging
import os
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

_SYSTEM = """You are a professional quantitative analyst and stock market expert.
You are given a list of stocks that triggered technical screening criteria (unusual price moves or trading volume).
Select the most promising candidates and explain concisely why each is worth watching.

Respond ONLY with a valid JSON array — no extra text, no markdown fences.
Each element must have exactly these keys:
  "ticker"    — string, the stock ticker
  "rank"      — integer starting at 1 (1 = most interesting)
  "signal"    — one of: BULLISH, BEARISH, NEUTRAL
  "rationale" — 1-2 sentences in {language} explaining the key reason to watch this stock

Return at most {top_n} candidates."""


async def rank_candidates(
    candidates: list[dict],
    language: str = "zh-TW",
    top_n: int = 8,
) -> list[dict]:
    """
    Call the watchlist LLM to rank and annotate screened candidates.
    Returns a list of dicts: ticker, rank, signal, rationale.
    Falls back to unranked list if LLM call fails.
    """
    if not candidates:
        return []

    llm_model = os.getenv("WATCHLIST_DEEP_THINK_LLM", "qwen2.5:14b-16k")
    base_url = os.getenv("WATCHLIST_DEEP_THINK_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("WATCHLIST_DEEP_THINK_API_KEY", "ollama")
    today = date.today().strftime("%Y-%m-%d")

    # Format candidates for the prompt
    lines = []
    for c in candidates:
        rsi_str = f"RSI={c['rsi']:.0f}" if c.get("rsi") is not None else "RSI=N/A"
        sign = "+" if c["price_change_pct"] >= 0 else ""
        lines.append(
            f"- {c['ticker']} ({c['market_type'].upper()}): "
            f"1d Δ{sign}{c['price_change_pct']:.2f}%, "
            f"Vol×{c['volume_ratio']:.1f}, {rsi_str}"
        )
    candidates_text = "\n".join(lines)

    system_prompt = _SYSTEM.format(language=language, top_n=top_n)
    user_prompt = (
        f"Today is {today}. Stocks that triggered our screener:\n\n"
        f"{candidates_text}\n\n"
        f"Return the top {top_n} as a JSON array."
    )

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        raw_text = response.choices[0].message.content or ""
        ranked = _parse_llm_response(raw_text)
        logger.info(f"LLM ranked {len(ranked)} candidates")
        return ranked
    except Exception as e:
        logger.error(f"LLM ranking failed: {e} — using unranked fallback")
        return [
            {"ticker": c["ticker"], "rank": i + 1, "signal": "NEUTRAL", "rationale": ""}
            for i, c in enumerate(candidates[:top_n])
        ]


_DETAIL_SYSTEM = """You are a professional stock market analyst specializing in technical analysis.
Write a detailed yet concise analysis report in {language} for the stock provided.
Use Markdown with clear ## section headers. Be specific, data-driven, and actionable.
Do NOT use LaTeX or math notation — use plain text for all numbers."""

_DETAIL_USER = """Stock: **{ticker}** ({market_type_label})
Analysis Date: {date}

**Screener Metrics**
| Metric | Value |
|---|---|
| 1-Day Price Change | {price_change:+.2f}% |
| Volume vs 20d Avg | {vol_ratio:.1f}× |
| RSI (14) | {rsi} |
| Current Price | {current_price} |
| 30-Day Range | {low_30d} – {high_30d} |

**Recent 10-Day Price History**
| Date | Close | High | Low | Volume |
|---|---|---|---|---|
{price_table}

AI Screener Signal: **{signal}**
Initial Rationale: {initial_rationale}

Write a comprehensive analysis report with these sections:
## 篩選原因 (Why Selected)
## 價格走勢分析 (Price Action)
## 交易量解讀 (Volume Analysis)
## RSI 訊號 (RSI Signal)
## 潛在催化劑 (Potential Catalysts)
## 風險因素 (Risk Factors)
## 結論與操作建議 (Conclusion)
"""

_DETAIL_USER_EN = """Stock: **{ticker}** ({market_type_label})
Analysis Date: {date}

**Screener Metrics**
| Metric | Value |
|---|---|
| 1-Day Price Change | {price_change:+.2f}% |
| Volume vs 20d Avg | {vol_ratio:.1f}× |
| RSI (14) | {rsi} |
| Current Price | {current_price} |
| 30-Day Range | {low_30d} – {high_30d} |

**Recent 10-Day Price History**
| Date | Close | High | Low | Volume |
|---|---|---|---|---|
{price_table}

AI Screener Signal: **{signal}**
Initial Rationale: {initial_rationale}

Write a comprehensive analysis report with these sections:
## Why Selected
## Price Action Analysis
## Volume Analysis
## RSI Signal
## Potential Catalysts
## Risk Factors
## Conclusion & Suggested Action
"""


async def generate_detail_report(
    ticker: str,
    market_type: str,
    candidate: dict,
    ticker_detail: dict,
    language: str = "zh-TW",
) -> str:
    """
    Generate a detailed markdown analysis report for a single candidate.
    Returns the markdown string; returns empty string on failure.
    """
    llm_model = os.getenv("WATCHLIST_DEEP_THINK_LLM", "qwen2.5:14b-16k")
    base_url = os.getenv("WATCHLIST_DEEP_THINK_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("WATCHLIST_DEEP_THINK_API_KEY", "ollama")
    today = date.today().strftime("%Y-%m-%d")

    market_labels = {"us": "US Stock", "twse": "TWSE", "tpex": "TPEx"}
    market_type_label = market_labels.get(market_type, market_type.upper())

    # Build price table rows
    rows = ticker_detail.get("recent_prices", [])
    price_table = "\n".join(
        f"| {r['date']} | {r['close']} | {r.get('high', 'N/A')} | {r.get('low', 'N/A')} | {r.get('volume', 0):,} |"
        for r in rows
    ) or "| N/A | N/A | N/A | N/A | N/A |"

    rsi_val = ticker_detail.get("rsi") or candidate.get("rsi")
    rsi_str = f"{rsi_val:.1f}" if rsi_val is not None else "N/A"
    current_price = ticker_detail.get("current_price") or "N/A"
    low_30d = ticker_detail.get("price_low_30d") or "N/A"
    high_30d = ticker_detail.get("price_high_30d") or "N/A"
    price_change = ticker_detail.get("price_change_pct") or candidate.get("price_change_pct") or 0.0
    vol_ratio = ticker_detail.get("volume_ratio") or candidate.get("volume_ratio") or 1.0

    template = _DETAIL_USER if language != "en" else _DETAIL_USER_EN
    user_prompt = template.format(
        ticker=ticker,
        market_type_label=market_type_label,
        date=today,
        price_change=price_change,
        vol_ratio=vol_ratio,
        rsi=rsi_str,
        current_price=current_price,
        low_30d=low_30d,
        high_30d=high_30d,
        price_table=price_table,
        signal=candidate.get("signal", "NEUTRAL"),
        initial_rationale=candidate.get("rationale") or "N/A",
    )
    system_prompt = _DETAIL_SYSTEM.format(language=language)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=3000,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Detail report generation failed for {ticker}: {e}")
        return ""


def _parse_llm_response(text: str) -> list[dict]:
    """Extract and validate the JSON array from LLM output."""
    text = text.strip()

    # Strip markdown code fences
    if "```" in text:
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Find the JSON array boundaries
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        logger.warning(f"No JSON array found in LLM response: {text[:200]}")
        return []

    try:
        items = json.loads(text[start: end + 1])
        if not isinstance(items, list):
            return []

        valid_signals = {"BULLISH", "BEARISH", "NEUTRAL"}
        result = []
        for item in items:
            ticker = str(item.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            signal = str(item.get("signal", "NEUTRAL")).upper()
            if signal not in valid_signals:
                signal = "NEUTRAL"
            result.append({
                "ticker": ticker,
                "rank": int(item.get("rank", len(result) + 1)),
                "signal": signal,
                "rationale": str(item.get("rationale", ""))[:500],
            })

        result.sort(key=lambda x: x["rank"])
        return result
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}\nRaw: {text[:300]}")
        return []
