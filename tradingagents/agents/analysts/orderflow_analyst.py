from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
from datetime import datetime, timedelta
import re

from tradingagents.agents.utils.tick_tools import get_tick_microstructure
from tradingagents.agents.utils.core_stock_tools import get_stock_data
from tradingagents.agents.utils.prompts import get_agent_role_instruction, get_context_message


def create_orderflow_analyst(llm, language: str = "zh-TW"):
    """
    委託單流向分析師 — 專注於盤中微結構與資金流向分析。

    Taiwan stocks: uses intraday tick data (via Shioaji sidecar) for true order
    flow — VWAP position, buy/sell imbalance, block-trade footprint, session
    momentum.

    US stocks: no tick source available; falls back to daily OHLCV volume
    patterns — OBV trend, price-volume divergence, accumulation/distribution.
    """

    def orderflow_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state.get("company_name", ticker)

        is_taiwan = bool(re.fullmatch(r"\d{4,6}", ticker))

        tools = [get_tick_microstructure, get_stock_data]

        role_instruction = get_agent_role_instruction(language)
        context_msg = get_context_message(language, current_date, company_name, ticker)

        if language == "en":
            tick_note = (
                "• Call get_tick_microstructure(symbol, date) first to get intraday "
                "order flow data: VWAP, buy/sell imbalance, block trades, session momentum."
                if is_taiwan else
                "• Intraday tick data is only available for Taiwan stocks. "
                "Use get_stock_data for volume-based order flow analysis."
            )
            system_message = (
                "**Language Rule: Your ENTIRE response MUST be in English only.**\n\n"
                "【Professional Identity】\n"
                "You are a specialist order flow and market microstructure analyst. "
                "Your job is to decode the supply/demand dynamics hidden in trading "
                "activity — not price trends, not fundamentals, not news.\n\n"
                "【Analysis Focus】\n"
                "1. **Order Flow Imbalance**: Are buyers or sellers in control? "
                "The imbalance index (−1 to +1) quantifies net buying pressure.\n"
                "2. **VWAP Position**: Sustained trading above VWAP signals institutional "
                "accumulation; persistent below-VWAP closes reveal distribution.\n"
                "3. **Block Trade Activity**: Large lots (≥10,000 shares/tick) expose the "
                "institutional footprint and conviction behind the move.\n"
                "4. **Session Momentum**: Early-vs-late session drift reveals whether "
                "buyers or sellers have end-of-day urgency.\n"
                "5. **Volume Confirmation**: Does volume confirm or contradict the price "
                "trend? Divergences often precede reversals.\n\n"
                "【Tools】\n"
                f"{tick_note}\n"
                "• Call get_stock_data(symbol, start_date, end_date) for 30-day volume "
                "context to calibrate today's activity against recent norms.\n\n"
                "【Report Structure】\n"
                "1. Order Flow Summary (60-80 words): Dominant pressure and headline signal\n"
                "2. Microstructure Deep-Dive (200-300 words): VWAP, imbalance, block trades, "
                "session momentum with explicit interpretation of each metric\n"
                "3. Volume Context (80-120 words): Compare today's activity to the 30-day "
                "baseline; flag any anomalies\n"
                "4. Trading Implication (80-100 words): What does order flow signal for "
                "near-term price direction? Include conviction level.\n"
                "5. Key Metrics Table (required): Markdown table summarising all key figures\n\n"
                "**Language Rule: Your ENTIRE response MUST be in English only.**"
            )
        else:
            tick_note = (
                "• 請先呼叫 get_tick_microstructure(symbol, date) 取得盤中逐筆委託流向數據："
                "VWAP、買賣力道失衡指數、大單活動、盤中動能。"
                if is_taiwan else
                "• 逐筆交易資料僅支援台股。請使用 get_stock_data 進行成交量型態的資金流向分析。"
            )
            system_message = (
                "【專業身份】\n"
                "您是專業的委託單流向（Order Flow）與盤中微結構分析師。"
                "您的任務是解碼隱藏在交易活動中的供需動態——"
                "而非價格趨勢、基本面或新聞資訊。\n\n"
                "【分析重點】\n"
                "1. **買賣力道失衡**：主力在買還是在賣？"
                "失衡指數（−1 至 +1）量化淨買盤壓力。\n"
                "2. **VWAP 位置**：持續守在 VWAP 之上代表法人積極佈局；"
                "長期跌破 VWAP 代表機構出貨。\n"
                "3. **大單活動**：大批交易（≥10,000 股/筆）揭示法人足跡與持倉信心。\n"
                "4. **盤中動能**：早盤至尾盤的漂移方向，"
                "揭示買方還是賣方具有日內急迫性。\n"
                "5. **量價驗證**：成交量是否確認或背離當前價格走勢？"
                "背離往往預示趨勢反轉。\n\n"
                "【工具使用】\n"
                f"{tick_note}\n"
                "• 呼叫 get_stock_data(symbol, start_date, end_date) 取得30日成交量背景，"
                "以校準今日活動相對近期常態的水準。\n\n"
                "【報告架構】\n"
                "1. 委託流向摘要（60-80字）：主力方向與核心信號\n"
                "2. 微結構深度解析（200-300字）：VWAP、買賣失衡、大單分析、盤中動能——附明確解讀\n"
                "3. 量能背景（80-120字）：對比30日基準，標示任何異常\n"
                "4. 交易含義（80-100字）：委託流向對近期股價方向的啟示，包含信心程度\n"
                "5. 關鍵指標表格（必須）：Markdown 表格整理所有關鍵數據\n\n"
                "您的回覆必須完全使用繁體中文。"
            )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"{role_instruction}"
                " 您可以使用以下工具：{tool_names}。\n"
                "{system_message}"
                f"{context_msg}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))

        chain = prompt | llm.bind_tools(tools)

        start_date = (
            datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=30)
        ).strftime("%Y-%m-%d")

        messages = list(state["messages"])
        last = messages[-1] if messages else None

        if isinstance(last, HumanMessage):
            if is_taiwan:
                kickoff = (
                    f"Analyze order flow for {company_name} ({ticker}) on {current_date}. "
                    f"First call get_tick_microstructure with symbol={ticker}, date={current_date}. "
                    f"Then call get_stock_data with symbol={ticker}, "
                    f"start_date={start_date}, end_date={current_date} for 30-day volume context. "
                    f"Use these exact values."
                )
            else:
                kickoff = (
                    f"Analyze order flow and volume patterns for {company_name} ({ticker}) "
                    f"as of {current_date}. "
                    f"Call get_stock_data with symbol={ticker}, "
                    f"start_date={start_date}, end_date={current_date}. "
                    f"Focus on volume trends, price-volume divergence, and "
                    f"accumulation/distribution signals over the 30-day window."
                )
            messages[-1] = HumanMessage(content=kickoff)

        elif isinstance(last, ToolMessage):
            lang_note = (
                "Your ENTIRE response MUST be in English only."
                if language == "en"
                else "您的回覆必須完全使用繁體中文。"
            )
            messages.append(HumanMessage(content=(
                "You now have the order flow and volume data. "
                "Write your complete order flow analysis report now. "
                f"{lang_note} "
                "Do not ask for clarification — base your analysis entirely on the data received."
            )))

        result = chain.invoke(messages)

        report = state.get("orderflow_report", "")
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "orderflow_report": report,
        }

    return orderflow_analyst_node
