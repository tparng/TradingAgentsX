from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
from tradingagents.agents.utils.quant_tools import (
    get_quant_evaluation,
    get_institutional_flows,
    get_revenue_trend,
    get_valuation_metrics,
)
from tradingagents.agents.utils.prompts import get_agent_role_instruction


def create_quant_analyst(llm, language: str = "zh-TW"):
    """
    Create a quantitative analyst node that calls the stock-strategies scoring engine
    and writes a structured quant report.
    """

    def quant_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state.get("company_name", ticker)

        tools = [
            get_quant_evaluation,
            get_institutional_flows,
            get_revenue_trend,
            get_valuation_metrics,
        ]

        role_instruction = get_agent_role_instruction(language)

        if language == "en":
            system_message = (
                "**Language Rule: Your ENTIRE response MUST be written in English only. "
                "Do NOT use Chinese or any other language.**\n\n"
                "【Professional Identity】\n"
                "You are a senior quantitative analyst. Interpret structured scoring data "
                "from an algorithmic stock evaluation model and write a clear, actionable report.\n\n"
                "【Analysis Focus】\n"
                "1. **Composite Score**: Interpret the 0-100 score and BUY/WATCH/SKIP signal\n"
                "2. **Component Breakdown**: Analyze fundamental, technical, and backtest sub-scores\n"
                "3. **Trade Setup**: Entry price, stop-loss, target price, risk/reward ratio\n"
                "4. **Position Sizing**: Interpret suggested position size and rationale\n"
                "5. **Risk Notes**: Highlight model warnings and limitations\n"
                "6. **Taiwan Extras**: If institutional flow, revenue trend, or PER/PBR data is "
                "available, incorporate those insights\n\n"
                "【Report Structure】\n"
                "1. Quantitative Summary (60-80 words): Signal and composite score\n"
                "2. Score Breakdown (150-200 words): Fundamental / technical / backtest analysis\n"
                "3. Trade Setup (100-150 words): Entry/stop/target, position size, risk-reward\n"
                "4. Risk Assessment (80-100 words): Warnings and model limitations\n"
                "5. Data Table (required): Markdown table of key metrics\n\n"
                "**Language Rule: Your ENTIRE response MUST be written in English only.**"
            )
        else:
            system_message = (
                "【專業身份】\n"
                "您是資深量化分析師，負責解讀演算法股票評估模型的結構化評分數據，"
                "並撰寫清晰、具操作性的量化分析報告。\n\n"
                "【分析重點】\n"
                "1. **綜合評分**：解讀 0-100 評分及 BUY/WATCH/SKIP 信號\n"
                "2. **分項拆解**：分析基本面、技術面、回測勝率子評分\n"
                "3. **交易設定**：進場、停損、目標價位；評估風險報酬比\n"
                "4. **倉位建議**：解讀建議倉位大小及其理由\n"
                "5. **風險提示**：標示模型警告及局限性\n"
                "6. **台股專項**：如有法人籌碼、月營收趨勢、本益比/股價淨值比資料，請納入分析\n\n"
                "【報告架構】\n"
                "1. 量化摘要（60-80字）：整體信號與綜合評分解讀\n"
                "2. 評分拆解（150-200字）：基本面、技術面、回測分項詳細分析\n"
                "3. 交易設定（100-150字）：進場/停損/目標價、倉位大小、風險報酬分析\n"
                "4. 風險評估（80-100字）：風險提示及量化模型局限性\n"
                "5. 數據摘要表格（必須）：Markdown 表格整理關鍵指標\n\n"
                "請撰寫專業、數據驅動的量化分析報告。您的回覆必須完全使用繁體中文。"
            )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"{role_instruction}"
                " 您可以使用以下工具：{tool_names}。\n"
                "{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))

        chain = prompt | llm.bind_tools(tools)

        messages = list(state["messages"])
        last = messages[-1] if messages else None

        if isinstance(last, HumanMessage):
            messages[-1] = HumanMessage(content=(
                f"Run quantitative evaluation for {company_name} ({ticker}) as of {current_date}. "
                f"Use the get_quant_evaluation tool with ticker={ticker}, curr_date={current_date}. "
                f"Use these exact parameter values."
            ))
        elif isinstance(last, ToolMessage):
            lang_note = (
                "Your ENTIRE response MUST be in English only."
                if language == "en"
                else "您的回覆必須完全使用繁體中文。"
            )
            messages.append(HumanMessage(content=(
                "You now have the quantitative evaluation data. "
                "Write your complete quantitative analysis report now. "
                f"{lang_note} "
                "Do not ask for clarification — base your analysis entirely on the data received."
            )))

        result = chain.invoke(messages)

        report = state.get("quant_report", "")
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "quant_report": report,
        }

    return quant_analyst_node
