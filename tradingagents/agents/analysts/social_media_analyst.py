from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
import time
import json
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_news
from tradingagents.agents.utils.prompts import get_social_analyst_prompt, get_agent_role_instruction, get_context_message
from tradingagents.dataflows.config import get_config


def create_social_media_analyst(llm, language: str = "zh-TW"):
    """
    建立一個社群媒體分析師節點。

    Args:
        llm: 用於分析的語言模型。
        language: 報告語言 ('en' 或 'zh-TW')

    Returns:
        一個處理社群媒體分析的節點函式。
    """
    def social_media_analyst_node(state):
        """
        分析社群媒體貼文、近期公司新聞和公眾情緒。

        Args:
            state: 當前的代理狀態。

        Returns:
            更新後的代理狀態，包含情緒分析報告和訊息。
        """
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state.get("company_name", ticker)

        tools = [
            get_news,
        ]

        # Get language-specific prompts
        system_message = get_social_analyst_prompt(language)
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
        last = messages[-1] if messages else None
        if isinstance(last, HumanMessage):
            # First invocation: use natural language to avoid model echoing JSON text
            messages[-1] = HumanMessage(content=(
                f"Retrieve recent social media and news sentiment for {company_name} ({ticker}). "
                f"Use the get_news tool with ticker={ticker}, start_date={start_date}, end_date={current_date}. "
                f"Use these exact parameter values."
            ))
        elif isinstance(last, ToolMessage):
            lang_note = "Your ENTIRE response MUST be in English only." if language == "en" else "您的回覆必須完全使用繁體中文。"
            messages.append(HumanMessage(content=(
                "You now have the social media and news data. "
                "Write your complete market sentiment analysis report now. "
                f"{lang_note} "
                "Do not ask for clarification — base your analysis entirely on the data received."
            )))

        result = chain.invoke(messages)

        # Report logic: only save report when LLM gives final response
        report = state.get("sentiment_report", "")

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node