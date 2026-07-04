# -*- coding: utf-8 -*-
"""
TradingAgentsX TUI 進入點。

啟動方式:
    python -m tui.main
"""
from pathlib import Path

from dotenv import load_dotenv

# 從 .env 檔案載入環境變數（強制覆蓋系統環境變數）
load_dotenv(override=True)

from textual.app import App
from textual.theme import Theme

from tui.screens.config import ConfigScreen
from tui.screens.dashboard import DashboardScreen

# 歡迎橫幅 ASCII 藝術檔案路徑
STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------
# 自訂主題：交易終端風格（OLED 深色）
#   藍色作資料主色、琥珀色作重點/主要行動、紅綠作漲跌與危險操作。
# ---------------------------------------------------------------------------
TRADINGAGENTS_THEME = Theme(
    name="tradingagents",
    primary="#4C8DF6",     # 藍：資料主色、面板邊框、標題
    secondary="#7AA7FF",   # 淺藍：次要強調
    accent="#F5A524",      # 琥珀：主要行動 (CTA)、重點數字
    foreground="#E6EDF3",  # 近白（低白光）：正文
    background="#080B12",   # 午夜黑：OLED 底色
    surface="#121926",     # 卡片/面板底
    panel="#1B2432",       # 次層面板
    success="#3FB950",     # 綠：完成、買入
    warning="#F5A524",     # 琥珀：警告、持有
    error="#F26D6D",       # 紅：錯誤、賣出
    dark=True,
    variables={
        "border": "#2A3444",
        "border-blurred": "#222B39",
        "block-cursor-foreground": "#080B12",
        "footer-key-foreground": "#F5A524",
        "footer-description-foreground": "#8B98A9",
        "scrollbar": "#1B2432",
        "scrollbar-hover": "#2A3444",
        "scrollbar-active": "#4C8DF6",
        # 語意輔助色（供 .tcss / 程式引用）
        "text-muted": "#8B98A9",
    },
)


def _prewarm_multiprocessing() -> None:
    """
    在 Textual 接管終端機之前，先啟動 multiprocessing 的 resource_tracker。

    背景說明：
        分析過程用到的函式庫（chromadb、sentence-transformers 等）會建立
        multiprocessing 的號誌 (Semaphore)。第一次建立時，Python 會延遲啟動
        resource_tracker 輔助行程，並透過 fork_exec 傳遞一個管線 fd。
        然而一旦 Textual 接管了終端機（重導/關閉標準 fd），這個 fd 就會失效，
        導致 `ValueError: bad value(s) in fds_to_keep`，分析在抓資料階段即崩潰。

    解法：
        在啟動 TUI 之前先建立一個號誌，強制 resource_tracker 以正常的 fd 啟動；
        之後在 Textual 執行期間再建立號誌時，只會寫入既有的 tracker，不再 fork。
    """
    try:
        import multiprocessing as mp

        sem = mp.Semaphore(1)
        del sem
    except Exception:
        # 預熱失敗不應阻擋程式啟動；真的用到時才可能出錯。
        pass


class TradingAgentsXApp(App):
    """TradingAgentsX 的 Textual 應用程式。"""

    CSS_PATH = "app.tcss"
    TITLE = "TradingAgentsX"
    SUB_TITLE = "多代理 LLM 金融交易框架"

    def __init__(self) -> None:
        super().__init__()
        # 讀取歡迎橫幅
        welcome_file = STATIC_DIR / "welcome.txt"
        try:
            self.welcome_ascii = welcome_file.read_text(encoding="utf-8").rstrip("\n")
        except OSError:
            self.welcome_ascii = "TradingAgentsX"

    def on_mount(self) -> None:
        self.register_theme(TRADINGAGENTS_THEME)
        self.theme = "tradingagents"
        self.push_screen(ConfigScreen())

    def start_analysis(self, selections) -> None:
        """由設定畫面呼叫，切換到儀表板並開始分析。"""
        self.push_screen(DashboardScreen(selections))


def main() -> None:
    # 先預熱 multiprocessing，避免 Textual 接管終端後 fork 子行程失敗
    _prewarm_multiprocessing()
    TradingAgentsXApp().run()


if __name__ == "__main__":
    main()
