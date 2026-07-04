# -*- coding: utf-8 -*-
"""
儀表板畫面：即時顯示代理進度、訊息 / 工具呼叫、以及當前報告。
對應原本 CLI 用 rich.Live 呈現的版面。分析在背景執行緒中執行。
"""
from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from tui.analysis import run_analysis
from tui.message_buffer import MessageBuffer, TEAMS


# 語意色（與 main.py 的主題一致）
C_MUTED = "#8B98A9"
C_BLUE = "#7AA7FF"
C_AMBER = "#F5A524"
C_GREEN = "#3FB950"
C_RED = "#F26D6D"

# 狀態 → (符號 + 文字, 顏色)。以「符號 + 文字 + 顏色」三重編碼，不依賴顏色單獨表意。
STATUS_DISPLAY = {
    "pending": ("○ 等待", C_MUTED),
    "in_progress": ("◐ 進行中", C_AMBER),
    "completed": ("● 完成", C_GREEN),
    "error": ("✗ 錯誤", C_RED),
}

# 訊息類型 → 顏色
TYPE_COLOR = {
    "系統": C_MUTED,
    "推理": C_BLUE,
    "工具": C_AMBER,
    "分析": C_GREEN,
    "錯誤": C_RED,
}


def _decision_badge(decision) -> str:
    """依 BUY / SELL / HOLD 產生帶色的最終決策標記。"""
    d = str(decision).upper()
    if "BUY" in d:
        return f"[b {C_GREEN}]▲  最終決策　買入 BUY[/]"
    if "SELL" in d:
        return f"[b {C_RED}]▼  最終決策　賣出 SELL[/]"
    if "HOLD" in d:
        return f"[b {C_AMBER}]■  最終決策　持有 HOLD[/]"
    return f"[b {C_BLUE}]●  最終決策　{decision}[/]"


class DashboardScreen(Screen):
    """執行分析並即時顯示進度的主畫面。"""

    BINDINGS = [
        ("q", "quit", "離開"),
    ]

    def __init__(self, selections):
        super().__init__()
        self.config = selections
        self.buffer = MessageBuffer()
        self._finished = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self._summary_markup(), id="summary")
        with Horizontal(id="top"):
            with Vertical(id="progress-pane", classes="pane"):
                yield DataTable(id="progress", zebra_stripes=True)
            with Vertical(id="messages-pane", classes="pane"):
                yield DataTable(id="messages", zebra_stripes=True)
        with VerticalScroll(id="report-pane", classes="pane"):
            yield Markdown("*等待分析報告…*", id="report")
        yield Static(self._stats_markup(0, 0, 0), id="stats")
        yield Footer()

    def _summary_markup(self) -> str:
        c = self.config
        market = "美股" if c.get("market_type") == "us" else "台股"
        depth = {1: "淺層", 3: "中等", 5: "深層"}.get(
            c.get("research_depth"), c.get("research_depth")
        )
        sep = f"  [{C_MUTED}]│[/]  "
        parts = [
            f"[b {C_AMBER}]{c.get('ticker', '—')}[/]",
            market,
            str(c.get("analysis_date", "—")),
        ]
        if c.get("research_depth") is not None:
            parts.append(f"深度 {depth}")
        if c.get("shallow_thinker") and c.get("deep_thinker"):
            parts.append(
                f"[{C_MUTED}]模型[/] {c['shallow_thinker']} / {c['deep_thinker']}"
            )
        return sep.join(parts)

    def on_mount(self) -> None:
        self.app.title = (
            f"TradingAgentsX · {self.config['ticker']} · "
            f"{self.config['analysis_date']}"
        )

        progress = self.query_one("#progress", DataTable)
        progress.add_columns("團隊", "代理", "狀態")
        progress.cursor_type = "none"

        messages = self.query_one("#messages", DataTable)
        messages.add_columns("時間", "類型", "內容")
        messages.cursor_type = "row"

        # 面板標題（利用邊框標題，畫面更乾淨）
        self.query_one("#progress-pane").border_title = "進度"
        self.query_one("#messages-pane").border_title = "訊息與工具"
        self.query_one("#report-pane").border_title = "當前報告"

        self.refresh_display()
        # 在背景執行緒中執行分析，避免阻塞 UI
        self.run_worker(self._run_analysis, thread=True, exclusive=True)

    # ------------------------------------------------------------------
    # 背景 worker
    # ------------------------------------------------------------------
    def _run_analysis(self) -> None:
        def on_update():
            # 從 worker 執行緒安全地觸發 UI 重繪
            self.app.call_from_thread(self.refresh_display)

        try:
            final_state, decision = run_analysis(
                self.config, self.buffer, on_update
            )
            self.app.call_from_thread(self._on_complete, decision)
        except Exception as exc:  # noqa: BLE001 — 將任何錯誤顯示到 UI
            self.buffer.add_message("錯誤", f"分析失敗: {exc}")
            self.app.call_from_thread(self.refresh_display)
            self.app.call_from_thread(
                self.query_one("#stats", Static).update,
                f"[b {C_RED}]✗  分析失敗：{exc}[/]",
            )

    def _on_complete(self, decision) -> None:
        self._finished = True
        self.refresh_display()
        self.query_one("#stats", Static).update(_decision_badge(decision))

    # ------------------------------------------------------------------
    # 重繪
    # ------------------------------------------------------------------
    def refresh_display(self) -> None:
        self._refresh_progress()
        self._refresh_messages()
        self._refresh_report()
        self._refresh_stats()

    def _refresh_progress(self) -> None:
        table = self.query_one("#progress", DataTable)
        table.clear()
        for team, agents in TEAMS.items():
            for idx, agent in enumerate(agents):
                status = self.buffer.agent_status[agent]
                text, color = STATUS_DISPLAY.get(status, (status, "white"))
                team_cell = (
                    Text(team, style=f"bold {C_BLUE}") if idx == 0 else Text("")
                )
                table.add_row(
                    team_cell,
                    Text(agent, style=C_MUTED if status == "pending" else ""),
                    Text(text, style=color),
                )

    def _refresh_messages(self) -> None:
        table = self.query_one("#messages", DataTable)
        table.clear()
        recent, total = self.buffer.recent_messages(max_messages=100)
        for timestamp, msg_type, content in recent:
            table.add_row(
                Text(timestamp, style=C_MUTED),
                Text(msg_type, style=TYPE_COLOR.get(msg_type, "")),
                content,
            )
        # 捲動到最新一列
        if table.row_count:
            table.scroll_end(animate=False)

    def _refresh_report(self) -> None:
        report = self.buffer.final_report or self.buffer.current_report
        markdown = self.query_one("#report", Markdown)
        if report:
            markdown.update(report)
        else:
            markdown.update("*等待分析報告…*")

    def _stats_markup(self, tool_calls: int, llm_calls: int, reports: int) -> str:
        sep = f"   [{C_MUTED}]·[/]   "
        return (
            f"[{C_MUTED}]工具呼叫[/] [b {C_AMBER}]{tool_calls}[/]{sep}"
            f"[{C_MUTED}]LLM 呼叫[/] [b {C_AMBER}]{llm_calls}[/]{sep}"
            f"[{C_MUTED}]已生成報告[/] [b {C_AMBER}]{reports}[/]"
        )

    def _refresh_stats(self) -> None:
        tool_calls, llm_calls, reports = self.buffer.stats()
        if not self._finished:
            self.query_one("#stats", Static).update(
                self._stats_markup(tool_calls, llm_calls, reports)
            )

    def action_quit(self) -> None:
        self.app.exit()
