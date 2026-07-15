"""
Export TradingAgentsX JSON analysis results to readable Markdown files.
Output: report/<TICKER>/<TICKER>_Report_<DATE>.md
"""
import json
import os
from pathlib import Path


def extract_text(value) -> str:
    """Recursively extract text from string, dict, or list."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n\n".join(extract_text(v) for v in value if v)
    if isinstance(value, dict):
        parts = []
        for v in value.values():
            t = extract_text(v)
            if t:
                parts.append(t)
        return "\n\n".join(parts)
    return ""


def debate_to_md(state: dict, bull_key: str, bear_key: str, neutral_key: str = None) -> str:
    lines = []
    if state.get(bull_key):
        lines.append("#### 看漲方\n")
        lines.append(extract_text(state[bull_key]))
    if state.get(bear_key):
        lines.append("\n#### 看跌方\n")
        lines.append(extract_text(state[bear_key]))
    if neutral_key and state.get(neutral_key):
        lines.append("\n#### 中立方\n")
        lines.append(extract_text(state[neutral_key]))
    if state.get("judge_decision"):
        lines.append("\n#### 裁決\n")
        lines.append(extract_text(state["judge_decision"]))
    return "\n".join(lines)


def json_to_md(json_path: Path, out_dir: Path):
    with open(json_path) as f:
        data = json.load(f)

    for date_key, day in data.items():
        ticker = day.get("company_of_interest", json_path.parts[-3])
        trade_date = day.get("trade_date", date_key)

        md_path = out_dir / ticker / f"{ticker}_Report_{trade_date}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"# {ticker} 分析報告 — {trade_date}\n"]
        lines.append(f"> 由 TradingAgentsX 多代理 AI 系統生成\n")

        # ── Analyst reports ──────────────────────────────────────────────
        lines.append("---\n")
        lines.append("## 📊 市場技術分析\n")
        lines.append(extract_text(day.get("market_report")) or "_（無資料）_")

        lines.append("\n---\n")
        lines.append("## 📰 新聞分析\n")
        lines.append(extract_text(day.get("news_report")) or "_（無資料）_")

        lines.append("\n---\n")
        lines.append("## 💬 社群媒體情緒\n")
        lines.append(extract_text(day.get("sentiment_report")) or "_（無資料）_")

        lines.append("\n---\n")
        lines.append("## 📈 基本面分析\n")
        lines.append(extract_text(day.get("fundamentals_report")) or "_（無資料）_")

        if day.get("quant_report"):
            lines.append("\n---\n")
            lines.append("## 🔢 量化分析\n")
            lines.append(extract_text(day.get("quant_report")))

        # ── Research debate ───────────────────────────────────────────────
        lines.append("\n---\n")
        lines.append("## ⚖️ 研究辯論（看漲 vs 看跌）\n")
        inv = day.get("investment_debate_state", {})
        if isinstance(inv, dict):
            lines.append(debate_to_md(inv, "bull_history", "bear_history"))
        else:
            lines.append(extract_text(inv))

        lines.append("\n---\n")
        lines.append("## 📋 投資計劃\n")
        lines.append(extract_text(day.get("investment_plan")) or "_（無資料）_")

        lines.append("\n---\n")
        lines.append("## 🛡️ 交易員初步決策\n")
        lines.append(extract_text(day.get("trader_investment_decision")) or "_（無資料）_")

        # ── Risk debate ───────────────────────────────────────────────────
        lines.append("\n---\n")
        lines.append("## ⚠️ 風險辯論（激進 vs 保守 vs 中立）\n")
        risk = day.get("risk_debate_state", {})
        if isinstance(risk, dict):
            lines.append(debate_to_md(risk, "risky_history", "safe_history", "neutral_history"))
        else:
            lines.append(extract_text(risk))

        # ── Final decision ────────────────────────────────────────────────
        lines.append("\n---\n")
        lines.append("## 🎯 最終交易決策\n")
        lines.append(extract_text(day.get("final_trade_decision")) or "_（無資料）_")

        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"✓ {md_path}")


def main():
    root = Path(__file__).parent.parent
    eval_root = root / "eval_results"
    out_dir = root / "report"

    for json_file in sorted(eval_root.rglob("full_states_log_*.json")):
        json_to_md(json_file, out_dir)


if __name__ == "__main__":
    main()
