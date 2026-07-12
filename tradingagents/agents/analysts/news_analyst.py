from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
import time
import json
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.agents.utils.prompts import get_news_analyst_prompt, get_agent_role_instruction, get_context_message
from tradingagents.dataflows.config import get_config


def create_news_analyst(llm, language: str = "zh-TW"):
    """
    建立一個新聞分析師節點。

    Args:
        llm: 用於分析的語言模型。
        language: 報告語言 ('en' 或 'zh-TW')

    Returns:
        一個處理新聞分析的節點函式。
    """
    def news_analyst_node(state):
        """
        分析最近的新聞和趨勢。

        Args:
            state: 當前的代理狀態。

        Returns:
            更新後的代理狀態，包含新聞分析報告和訊息。
        """
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state.get("company_name", ticker)

        tools = [
            get_news,
            get_global_news,
        ]

        # Get language-specific prompts
        system_message = get_news_analyst_prompt(language)
        role_instruction = get_agent_role_instruction(language)
        context_msg = get_context_message(language, current_date, company_name, ticker)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"{role_instruction}"
                    " 您可以使用以下工具：{tool_names}。\n{system_message}"
                    f" {context_msg}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

        chain = prompt | llm.bind_tools(tools)

        # Pre-compute explicit parameters so the model doesn't need to infer them
        start_date = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        messages = list(state["messages"])
        if messages and isinstance(messages[-1], HumanMessage):
            messages[-1] = HumanMessage(content=(
                f"Analyze {company_name} ({ticker}) news as of {current_date}. "
                f"Call get_news(ticker='{ticker}', start_date='{start_date}', end_date='{current_date}') now. "
                f"Do not ask for any parameters — use exactly these values."
            ))

        result = chain.invoke(messages)

        # Report logic: only save report when LLM gives final response
        report = state.get("news_report", "")

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node