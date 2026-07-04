# -*- coding: utf-8 -*-
"""
訊息緩衝區：儲存並管理分析過程中的訊息、工具呼叫、代理狀態與報告區塊。
從 cli/main.py 的 MessageBuffer 移植而來，與任何 UI 框架解耦，
Textual 的儀表板畫面會讀取這裡的狀態來渲染。
"""
import datetime
from collections import deque


# 報告區塊代碼 → 中文標題
SECTION_TITLES = {
    "market_report": "市場分析",
    "sentiment_report": "社群情緒",
    "news_report": "新聞分析",
    "fundamentals_report": "基本面分析",
    "investment_plan": "研究團隊決策",
    "trader_investment_plan": "交易團隊計畫",
    "final_trade_decision": "投資組合管理決策",
}

# 代理團隊分組（用於進度面板）
TEAMS = {
    "分析師團隊": [
        "Market Analyst",
        "Social Analyst",
        "News Analyst",
        "Fundamentals Analyst",
    ],
    "研究團隊": ["Bull Researcher", "Bear Researcher", "Research Manager"],
    "交易團隊": ["Trader"],
    "風險管理": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"],
    "投資組合管理": ["Portfolio Manager"],
}


class MessageBuffer:
    """用於儲存和管理應用程式訊息、工具呼叫和報告狀態的緩衝區。"""

    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None  # 當前顯示的報告部分
        self.final_report = None  # 儲存完整的最終報告
        # 代理狀態字典，追蹤每個代理的進度
        self.agent_status = {
            # 分析師團隊
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            # 研究團隊
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # 交易團隊
            "Trader": "pending",
            # 風險管理團隊
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # 投資組合管理團隊
            "Portfolio Manager": "pending",
        }
        self.current_agent = None  # 當前正在執行的代理
        # 報告區塊字典，儲存分析過程中的各個報告
        self.report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

    def add_message(self, message_type, content):
        """新增一條訊息到緩衝區。"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        """新增一條工具呼叫記錄到緩衝區。"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        """更新代理的狀態。"""
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        """更新報告的特定區塊。"""
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        """更新當前用於顯示的報告。"""
        latest_section = None
        latest_content = None

        # 找到最近更新的部分
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content

        if latest_section and latest_content:
            self.current_report = (
                f"### {SECTION_TITLES[latest_section]}\n{latest_content}"
            )

        # 更新完整的最終報告
        self._update_final_report()

    def _update_final_report(self):
        """更新完整的最終報告。"""
        report_parts = []

        # 分析師團隊報告
        if any(
            self.report_sections[section]
            for section in [
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
            ]
        ):
            report_parts.append("## 分析師團隊報告")
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### 市場分析\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### 社群情緒\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### 新聞分析\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### 基本面分析\n{self.report_sections['fundamentals_report']}"
                )

        # 研究團隊報告
        if self.report_sections["investment_plan"]:
            report_parts.append("## 研究團隊決策")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # 交易團隊報告
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## 交易團隊計畫")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")

        # 投資組合管理決策
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## 投資組合管理決策")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None

    # ------------------------------------------------------------------
    # 供 UI 使用的輔助方法
    # ------------------------------------------------------------------
    def recent_messages(self, max_messages=100):
        """合併工具呼叫與一般訊息，依時間排序後回傳最近 N 筆。"""
        all_messages = []

        # 工具呼叫
        for timestamp, tool_name, args in self.tool_calls:
            if isinstance(args, str) and len(args) > 100:
                args = args[:97] + "..."
            all_messages.append((timestamp, "工具", f"{tool_name}: {args}"))

        # 一般訊息
        for timestamp, msg_type, content in self.messages:
            content_str = _content_to_str(content)
            if len(content_str) > 200:
                content_str = content_str[:197] + "..."
            all_messages.append((timestamp, msg_type, content_str))

        all_messages.sort(key=lambda x: x[0])
        return all_messages[-max_messages:], len(all_messages)

    def stats(self):
        """回傳 (工具呼叫數, LLM 呼叫數, 已生成報告數)。"""
        tool_calls_count = len(self.tool_calls)
        llm_calls_count = sum(
            1 for _, msg_type, _ in self.messages if msg_type in ("推理", "Reasoning")
        )
        reports_count = sum(
            1 for content in self.report_sections.values() if content is not None
        )
        return tool_calls_count, llm_calls_count, reports_count


def _content_to_str(content):
    """將訊息內容（可能是 Anthropic 的區塊列表）轉換為純字串。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    text_parts.append(f"[工具: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return " ".join(text_parts)
    return str(content)
