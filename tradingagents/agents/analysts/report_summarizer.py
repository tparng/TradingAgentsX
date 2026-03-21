"""
Report Summarizer — 將 4 份分析師報告壓縮成 ~600 字的單一結構化摘要。

用途：在 Bull/Bear 研究員和風險辯論員收到報告之前，
先用 quick_thinking_llm 壓縮，減少下游 agent 的 input tokens（節省約 75% 費用）。
"""

from langchain_core.messages import HumanMessage

from tradingagents.agents.utils.agent_utils import make_cached_system_message
from tradingagents.agents.utils.output_filter import _normalize_content
from tradingagents.agents.utils.prompts import get_report_summarizer_prompt


def create_report_summarizer(llm, language: str = "zh-TW"):
    """建立 Report Summarizer 節點。

    Args:
        llm: quick_thinking_llm（使用者設定的輕量模型）
        language: 輸出語言，"en" 或 "zh-TW"

    Returns:
        LangGraph 節點函式 node(state) -> dict
    """

    def summarizer_node(state) -> dict:
        market_report       = state.get("market_report", "")
        sentiment_report    = state.get("sentiment_report", "")
        news_report         = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")

        # 取得 system prompt（並透過 make_cached_system_message 自動判斷是否加 cache_control）
        system_prompt = get_report_summarizer_prompt(language)

        # 組合原始報告作為 human message（動態資料，不快取）
        if language == "en":
            data_block = (
                f"[Market Analysis]\n{market_report or 'Data unavailable'}\n\n"
                f"[Sentiment Analysis]\n{sentiment_report or 'Data unavailable'}\n\n"
                f"[News Analysis]\n{news_report or 'Data unavailable'}\n\n"
                f"[Fundamentals Analysis]\n{fundamentals_report or 'Data unavailable'}"
            )
            human_text = f"Please summarize the following four analyst reports:\n\n{data_block}"
        else:
            data_block = (
                f"【市場分析】\n{market_report or '無資料'}\n\n"
                f"【社群情緒】\n{sentiment_report or '無資料'}\n\n"
                f"【新聞分析】\n{news_report or '無資料'}\n\n"
                f"【基本面分析】\n{fundamentals_report or '無資料'}"
            )
            human_text = f"請摘要以下四份分析師報告：\n\n{data_block}"

        messages = [
            make_cached_system_message(system_prompt, llm),  # Claude → cache_control；其他 → 普通
            HumanMessage(content=human_text),
        ]

        try:
            response = llm.invoke(messages)
            summary = _normalize_content(response.content) if response.content else ""
        except Exception as e:
            # 失敗時回傳空字串，不中斷整個 graph 執行
            print(f"[Report Summarizer] 摘要生成失敗，使用空摘要: {e}")
            summary = ""

        return {"analyst_summary": summary}

    return summarizer_node
