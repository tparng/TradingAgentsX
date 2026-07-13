# TradingAgentsX - 多代理智能交易分析系統

<div align="center">

<img src="frontend/public/icon-v8.png" alt="TradingAgentsX Logo" width="300" />

**基於 LangGraph 的 AI 股票交易分析平台，結合多個專業 AI 代理進行協作決策**

[![GitHub](https://img.shields.io/badge/GitHub-MarkLo127/TradingAgentsX-blue?logo=github)](https://github.com/MarkLo127/TradingAgentsX)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

[![Deploy on Railway](https://railway.app/button.svg)](https://tradingagentsx.up.railway.app)

</div>

---

## 📖 簡介

**TradingAgentsX** 是一個先進的多代理 AI 交易分析系統，模擬真實世界的交易公司運作模式。透過 LangGraph 編排多個專業化的 AI 代理（分析師、研究員、交易員、風險管理者），系統能夠從不同角度分析股票市場，並通過結構化的辯論與協作流程產生高質量的交易決策。

> 💡 **致敬原作**: 本專案基於 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 進行改進和擴展。

### 🎯 核心特色

| 功能                     | 說明                                                            |
| ------------------------ | --------------------------------------------------------------- |
| 🤖 **多代理協作架構**    | 12 個專業化 AI 代理（分析師、研究員、交易員、風險管理）協同工作 |
| 🌐 **多模型支援**        | Ollama（本地）、OpenAI、Anthropic、Gemini、Grok、DeepSeek、Qwen 等 LLM 提供商   |
| 🔒 **Google OAuth 登入** | 雲端同步 API 設定與歷史報告，支援多裝置同步                     |
| 📊 **美股與台股支援**    | 完整支援美股（Yahoo Finance）與台股（FinMind）資料              |
| 🔑 **BYOK 模式**         | 使用者自帶 API 金鑰，前端加密儲存，保障隱私                     |
| 🛡️ **安全防護**          | Rate Limiting、Security Headers、API Key 遮罩                   |
| 📱 **響應式設計**        | 支援桌面與手機瀏覽器                                            |
| 🐳 **Docker 部署**       | 一鍵啟動前後端服務                                              |
| 🧠 **Embeddings 模型選擇** | 支援 sentence-transformers（本地免費）或 OpenAI embeddings      |
| 💬 **AI報告問答**        | 支援AI問答功能                                                  |
| 📊 **PDF預覽**           | 支援PDF預覽功能                                                 |
| 🌐 **多語言支援**        | 支援繁體中文、英文                                              |
| 📈 **即時交易**          | 整合 Sinopac Shioaji API，支援台股即時報價、下單、持倉管理（模擬模式預設開啟） |

---

## 🔧 近期變更

### v5 改進（當前版本）

| 變更項目 | 說明 |
| -------- | ---- |
| **新增即時交易功能** | 整合 Sinopac Shioaji API，支援台股即時報價、下單、查詢持倉、取消委託等功能 |
| **模擬交易預設開啟** | 預設啟用紙上交易（simulation=True），避免誤用真實帳戶 |
| **Session 管理** | 以 UUID 作為 session key，8 小時 TTL，threading.Lock 保護並發存取；前端僅存 session_id（不存 API 金鑰） |
| **REST API 端點** | `/api/trading/*` 下新增 8 個端點（connect、disconnect、quote、balance、positions、order CRUD、list orders），全部以 `asyncio.to_thread()` 包裝阻塞式 Shioaji 呼叫 |
| **即時交易 UI** | 新增 `/trading` 頁面，含連線卡片（API 金鑰輸入、模擬/真實切換）及四個分頁：即時報價、下單、持倉、今日委託 |
| **導覽列新增交易連結** | Header 桌面版與手機版導覽列新增「Trading / 即時交易」連結，可直接跳轉至 `/trading` 頁面 |
| **修復「Failed to fetch」** | 交易頁改用相對路徑 `/api/trading/*`，請求透過 Next.js catch-all proxy 轉發至後端，與其他頁面一致，解決瀏覽器直連 `localhost:8000` 失敗的問題 |
| **加密儲存 API 金鑰** | 連線成功後以 AES-256-GCM（`lib/crypto.ts`）加密 Sinopac API Key / Secret Key 並存入 localStorage；下次開啟頁面自動預填，並提供「Clear saved credentials」清除連結 |
| **新增缺少的 UI 元件** | 補充 `components/ui/alert.tsx`（shadcn Alert/AlertDescription）及 `components/ui/switch.tsx`（純 CSS 切換開關，不依賴 @radix-ui/react-switch）|
| **一鍵啟動腳本** | 新增 `start.sh`：自動啟動後端、前端及 shioaji-pro-app、等待服務就緒後開啟 Chrome；支援已啟動時跳過重複啟動；搭配 Ubuntu 桌面捷徑（`.desktop` 檔）可雙擊圖示啟動，無需輸入指令 |
| **整合 Shioaji Pro Terminal** | 整合 [shioaji-pro-app](https://github.com/Sinotrade/shioaji-pro-app) 全功能交易終端（AGPL-3.0）；後端以 `ShioajiServerManager` 管理 sidecar binary（port 21322），新增 `/api/shioaji-server/{start,stop,status}` 3 個端點；`/trading` 頁面新增「Shioaji Pro Terminal」卡片，一鍵啟動伺服器並在新分頁開啟完整交易介面（port 5173） |
| **修復 Sidecar 啟動方式** | Sidecar binary 不接受 `--api-key` / `--secret-key` / `--port` CLI 參數；改以環境變數傳入（`SJ_API_KEY`、`SJ_SEC_KEY`、`SJ_HTTP_ADDR`、`SJ_PRODUCTION`），指令改為 `server start --no-open` |

### v4 改進

| 變更項目 | 說明 |
| -------- | ---- |
| **新增量化分析師** | 整合 `stock-strategies-only` 量化引擎，新增第 5 位分析師節點（量化分析師），產出綜合評分（0-100）、分項評分、進場/停損/目標價、倉位建議與回測勝率 |
| **4 個量化工具** | 新增 `get_quant_evaluation`（美股/台股通用）、`get_institutional_flows`、`get_revenue_trend`、`get_valuation_metrics`（台股專用）等 LangChain 工具 |
| **sys.path 整合** | 透過 `sys.path` 動態掛載 `../stock-strategies-only`，無需 pip install，保持兩個儲存庫各自獨立 |

### v3 改進

| 變更項目 | 說明 |
| -------- | ---- |
| **報告語言切換器** | 分析表單新增「報告語言」下拉選單，可獨立於 UI 語言選擇 AI 報告語言（繁體中文 / English） |
| **修復英文語言合規** | 所有 4 個分析師節點在工具回傳資料後注入明確語言提醒（`lang_note`），防止 qwen2.5:14b 在報告中切換成其他語言 |
| **消除重複終端輸出** | `trading_graph.py` 追蹤 `last_printed_id`，跳過已顯示訊息，修復風險辯論節點導致交易者訊息重複顯示 5 次的問題 |
| **除錯訊息英文化** | `interface.py` 所有中文除錯輸出（`調試:`、`失敗:`、`成功:` 等）統一改為英文 `[vendor]` 格式 |

### v2 改進

| 變更項目 | 說明 |
| -------- | ---- |
| **預設 LLM 切換為 Ollama** | 預設使用 `qwen2.5:14b`（本地推理），無需 OpenAI API 金鑰 |
| **套件管理切換為 uv** | 取代 conda，使用 `uv sync` + `uv pip install -r backend/requirements.txt` 安裝依賴 |
| **新聞資料來源調整** | `news_data` 改用 `google`（Google News RSS，無需 API 金鑰），`get_global_news` 改用 `local`（Reddit） |
| **修復分析師工具呼叫** | 為每個分析師節點注入含預計算參數的明確啟動訊息，解決小型本地模型（如 qwen2.5:14b）不呼叫工具而改為詢問用戶的問題 |
| **修復 polars 匯入問題** | 5 個 dataflow 檔案改用 `try/except ImportError` 保護，避免後端啟動時崩潰 |
| **TUI 新增 Ollama 支援** | Terminal UI 新增 Ollama 提供商選項，模型格式含 `:` 時自動識別為 Ollama |

---

## 📝 與原始儲存庫的差異檔案清單

以下列出相對於原始 [`MarkLo127/TradingAgentsX`](https://github.com/MarkLo127/TradingAgentsX) 儲存庫，本分支新增或修改的檔案及其原因。

### 核心代理邏輯

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `tradingagents/agents/analysts/quant_analyst.py` | **新增** | 量化分析師節點；呼叫 `get_quant_evaluation` 取得結構化評分資料，再由 LLM 撰寫量化分析報告 |
| `tradingagents/agents/utils/quant_tools.py` | **新增** | 4 個 LangChain StructuredTool：`get_quant_evaluation`（美股/台股）、`get_institutional_flows`、`get_revenue_trend`、`get_valuation_metrics`（台股專用）；透過 `sys.path` 掛載 stock-strategies-only |
| `tradingagents/agents/utils/agent_states.py` | 修改 | `AgentState` 新增 `quant_report` 欄位 |
| `tradingagents/agents/analysts/market_analyst.py` | 修改 | 注入含預計算日期的明確啟動訊息；在工具回傳後注入「立即撰寫報告」指令及語言提醒，解決 qwen2.5:14b 不呼叫工具與語言切換問題 |
| `tradingagents/agents/analysts/news_analyst.py` | 修改 | 同上，針對新聞分析師節點 |
| `tradingagents/agents/analysts/social_media_analyst.py` | 修改 | 同上，針對社群媒體分析師節點 |
| `tradingagents/agents/analysts/fundamentals_analyst.py` | 修改 | 同上，針對基本面分析師節點 |
| `tradingagents/agents/utils/agent_utils.py` | 修改 | `create_msg_delete()` 的佔位訊息改為包含 ticker 與日期；重新匯出量化工具 |
| `tradingagents/graph/conditional_logic.py` | 修改 | 新增 `should_continue_quant()` 路由方法 |
| `tradingagents/graph/setup.py` | 修改 | 新增量化分析師節點配置區塊 |
| `tradingagents/graph/trading_graph.py` | 修改 | 匯入量化工具；新增 `quant` ToolNode；`_log_state()` 記錄 `quant_report`；以 `last_printed_id` 去重修復重複輸出 |

### 資料流層

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `tradingagents/default_config.py` | 修改 | 預設 LLM 改為 Ollama/qwen2.5:14b；新聞來源改為 Google News RSS（無需 API 金鑰）；全域新聞改為 local/Reddit |
| `tradingagents/dataflows/interface.py` | 修改 | 所有中文除錯輸出改為英文 `[vendor]` 格式；錯誤訊息英文化 |
| `tradingagents/dataflows/local.py` | 修改 | 頂層 `import polars` 改為 `try/except ImportError`，避免未安裝 polars 時後端啟動崩潰 |
| `tradingagents/dataflows/alpha_vantage_common.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/stockstats_utils.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/utils.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/yfin_utils.py` | 修改 | 同上，防護性 polars 匯入 |

### 後端

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `backend/app/models/schemas.py` | 修改 | `AnalysisRequest` 新增 `language` 欄位，接收前端傳入的報告語言設定 |
| `backend/app/services/trading_service.py` | 修改 | 將 `language` 傳入 `TradingAgentsXGraph` 設定；結果字典新增 `quant_report` |
| `backend/app/services/shioaji_service.py` | **新增** | `ShioajiSessionManager` 單例：以 UUID 管理 Shioaji 連線（8 小時 TTL、threading.Lock），封裝報價、餘額、持倉、下單、取消委託等操作 |
| `backend/app/api/trading_routes.py` | **新增** | 8 個 `/api/trading/*` REST 端點，以 `asyncio.to_thread()` 包裝阻塞式 Shioaji 呼叫以相容 FastAPI 非同步環境 |
| `backend/app/services/shioaji_server_service.py` | **新增** | `ShioajiServerManager` 單例：管理 shioaji-pro-app sidecar binary 的生命週期（啟動、停止、輪詢 `/api/v1/health` 健康狀態），port 21322；憑證以環境變數傳入（`SJ_API_KEY`、`SJ_SEC_KEY`、`SJ_HTTP_ADDR`），指令為 `server start --no-open` |
| `backend/app/api/shioaji_server_routes.py` | **新增** | 3 個 `/api/shioaji-server/*` REST 端點：`POST /start`（啟動 sidecar）、`POST /stop`（停止）、`GET /status`（回傳 running/healthy/pid） |
| `backend/app/main.py` | 修改 | 匯入並註冊 `trading_router` 及 `shioaji_server_router` |

### 前端

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `frontend/components/analysis/AnalysisForm.tsx` | 修改 | 新增「報告語言」下拉選單（繁體中文 / English）；新增「量化分析師」選項至分析師勾選清單 |
| `frontend/lib/i18n/en.ts` | 修改 | 新增報告語言選單、量化分析師、即時交易（~50 鍵）及導覽列 `trading` 鍵的英文 i18n 字串 |
| `frontend/lib/i18n/zh-TW.ts` | 修改 | 新增報告語言選單、量化分析師、即時交易（~50 鍵）及導覽列 `trading` 鍵的繁體中文 i18n 字串 |
| `frontend/app/trading/page.tsx` | 修改 | 新增「Shioaji Pro Terminal」卡片：呼叫 `/api/shioaji-server/start` 啟動 sidecar；sidecar 就緒後顯示「Open Pro Terminal」按鈕（在新分頁開啟 `localhost:5173`）；保留原有簡易交易 UI（四分頁）作為替代方案；憑證與下方連線卡片共用 |
| `frontend/components/layout/Header.tsx` | 修改 | 桌面版與手機版導覽列新增「Trading / 即時交易」連結 |
| `frontend/components/ui/alert.tsx` | **新增** | shadcn 標準 Alert / AlertTitle / AlertDescription 元件（交易頁警示用） |
| `frontend/components/ui/switch.tsx` | **新增** | 純 CSS 切換開關元件，不依賴 `@radix-ui/react-switch`（未安裝）；以 `<input type="checkbox">` 搭配 Tailwind peer 類實作 |
| `start.sh` | 修改 | 新增啟動 shioaji-pro-app 開發伺服器（port 5173）；偵測三個服務是否已啟動（跳過重複）；日誌輸出至 `/tmp/tradingagentsx-shioaji-app.log` |
| `.gitignore` | 修改 | 新增 `shioaji-pro-app/`（含 sidecar binary 的獨立 git 儲存庫，不納入版本控制） |

### TUI（終端機介面）

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `tui/analysis.py` | 修改 | 新增 Ollama 提供商支援；模型名稱含 `:` 時自動識別為 Ollama |
| `tui/constants.py` | 修改 | 新增 Ollama 至提供商常數清單 |
| `tui/screens/config.py` | 修改 | TUI 設定畫面新增 Ollama 選項 |

---

## 🏗️ 系統架構

```
TradingAgentsX/
├── frontend/                   # Next.js 前端應用
│   ├── app/                    # App Router 頁面
│   │   ├── page.tsx            # 首頁
│   │   ├── layout.tsx          # 根佈局
│   │   ├── globals.css         # 全域樣式
│   │   ├── analysis/           # 分析功能頁面
│   │   ├── history/            # 歷史報告頁面
│   │   ├── auth/               # OAuth 回調
│   │   └── api/                # API 路由（config, auth）
│   ├── components/             # React 組件
│   │   ├── AgentFlowDiagram.tsx    # 代理流程圖組件
│   │   ├── PendingTaskRecovery.tsx # 任務恢復組件
│   │   ├── analysis/           # 分析相關組件
│   │   ├── auth/               # 登入按鈕
│   │   ├── layout/             # Header、Footer
│   │   ├── settings/           # API 設定對話框
│   │   ├── shared/             # 共用組件
│   │   ├── theme/              # 主題相關組件
│   │   └── ui/                 # shadcn/ui 基礎組件（16 個）
│   ├── contexts/               # React Context（認證狀態）
│   ├── hooks/                  # 自定義 Hooks
│   └── lib/                    # 工具函式
│       ├── api.ts              # API 調用
│       ├── api-helpers.ts      # API 輔助函式
│       ├── crypto.ts           # 加密工具
│       ├── storage.ts          # 本地儲存
│       ├── reports-db.ts       # IndexedDB 報告儲存
│       ├── pending-task.ts     # 待處理任務管理
│       ├── user-api.ts         # 使用者 API
│       ├── types.ts            # TypeScript 類型定義
│       └── utils.ts            # 通用工具
│
├── backend/                    # FastAPI 後端服務
│   ├── __main__.py             # 應用啟動入口
│   └── app/
│       ├── main.py             # FastAPI 應用（中間件、路由）
│       ├── api/                # API 路由
│       │   ├── routes.py       # 分析 API
│       │   ├── auth.py         # Google OAuth
│       │   ├── user.py         # 使用者資料同步
│       │   ├── trading_routes.py       # 即時交易 API（Python shioaji 套件）
│       │   ├── shioaji_server_routes.py # Sidecar 管理 API（start/stop/status）
│       │   └── dependencies.py # 依賴注入
│       ├── core/               # 核心配置
│       ├── db/                 # PostgreSQL 資料庫
│       ├── models/             # Pydantic 模型
│       └── services/           # 業務邏輯
│           ├── trading_service.py      # 交易分析服務
│           ├── shioaji_service.py      # Shioaji Python lib session 管理
│           ├── shioaji_server_service.py # Sidecar binary 生命週期管理
│           ├── task_manager.py     # 任務管理器
│           ├── pdf_generator.py    # PDF 報告生成
│           ├── price_service.py    # 股價數據服務
│           ├── download_service.py # 下載服務
│           ├── redis_client.py     # Redis 客戶端
│           └── auth_utils.py       # 認證工具
│
├── shioaji-pro-app/            # 全功能交易終端（git clone 自 Sinotrade/shioaji-pro-app，不納入版控）
│   ├── src/                    # React/Vite 前端（port 5173）
│   └── src-tauri/binaries/     # Sidecar binary（需手動下載，port 21322）
│
└── tradingagents/              # 核心 AI 代理套件
    ├── agents/                 # AI 代理定義
    │   ├── analysts/           # 分析師團隊
    │   │   ├── market_analyst.py       # 市場分析師
    │   │   ├── news_analyst.py         # 新聞分析師
    │   │   ├── social_media_analyst.py # 社群媒體分析師
    │   │   └── fundamentals_analyst.py # 基本面分析師
    │   ├── researchers/        # 研究團隊
    │   │   ├── bull_researcher.py      # 看漲研究員
    │   │   └── bear_researcher.py      # 看跌研究員
    │   ├── trader/             # 交易員
    │   │   └── trader.py               # 交易員代理
    │   ├── risk_mgmt/          # 風險管理團隊
    │   │   ├── aggresive_debator.py    # 激進分析師
    │   │   ├── conservative_debator.py # 保守分析師
    │   │   └── neutral_debator.py      # 中立分析師
    │   ├── managers/           # 經理決策者
    │   │   ├── research_manager.py     # 研究經理
    │   │   └── risk_manager.py         # 風險經理
    │   └── utils/              # 代理工具函式
    ├── dataflows/              # 資料獲取與處理
    │   ├── interface.py        # 統一資料介面
    │   ├── config.py           # 資料流配置
    │   ├── y_finance.py        # Yahoo Finance 資料
    │   ├── yfin_utils.py       # Yahoo Finance 工具
    │   ├── alpha_vantage*.py   # Alpha Vantage 系列（5 個）
    │   ├── finmind*.py         # FinMind 台股資料（6 個）
    │   ├── google.py           # Google 搜尋
    │   ├── googlenews_utils.py # Google 新聞工具
    │   ├── reddit_utils.py     # Reddit 資料
    │   ├── openai.py           # OpenAI 嵌入
    │   └── retry_utils.py      # 重試工具
    ├── graph/                  # LangGraph 工作流
    │   ├── trading_graph.py    # 交易分析圖
    │   ├── setup.py            # 圖設置
    │   ├── propagation.py      # 狀態傳播
    │   ├── reflection.py       # 反思機制
    │   ├── conditional_logic.py    # 條件邏輯
    │   └── signal_processing.py    # 信號處理
    ├── utils/                  # 通用工具
    └── default_config.py       # 預設配置
```

---

## 🤖 AI 代理團隊

### 分析師團隊 (4 位)

| 代理           | 職責     | 輸出                                |
| -------------- | -------- | ----------------------------------- |
| 市場分析師     | 技術分析 | RSI、MACD、布林通道、支撐阻力位     |
| 社群媒體分析師 | 情緒評估 | Reddit/Twitter 情緒指標、投資者信心 |
| 新聞分析師     | 新聞分析 | 最新新聞摘要、事件影響評估          |
| 基本面分析師   | 財務分析 | 財報數據、P/E、P/B、盈利能力        |

> **注意（本地模型適配）**：每位分析師啟動時會收到含預計算參數的明確指令（如 `start_date`、`end_date`），確保 qwen2.5:14b 等小型本地模型能正確呼叫工具取得真實資料，而非生成詢問文字。

### 研究團隊 (3 位)

| 代理       | 職責                         |
| ---------- | ---------------------------- |
| 看漲研究員 | 多頭觀點論證、上漲催化劑分析 |
| 看跌研究員 | 空頭觀點論證、下跌風險警告   |
| 研究經理   | 綜合看漲與看跌觀點的決策     |

### 交易與風險團隊 (5 位)

| 代理       | 職責                       |
| ---------- | -------------------------- |
| 交易員     | 整合所有報告，制定交易計劃 |
| 激進分析師 | 高風險高回報策略分析       |
| 保守分析師 | 穩健保守策略與風險控制     |
| 中立分析師 | 中立平衡策略評估           |
| 風險經理   | 風險管理綜合決策與最終建議 |

---

## 🚀 快速開始

### 前置要求

- **Python** 3.13+
- **uv** 套件管理器（[安裝說明](https://docs.astral.sh/uv/getting-started/installation/)）
- **Node.js** 18.x+ 或 **Bun** 1.x+
- **Ollama**（本地 LLM，[安裝說明](https://ollama.com/download)）

### API 金鑰

預設使用 Ollama 本地模型，**無需任何 LLM API 金鑰**。

| API                   | 用途              | 申請網址                                     |
| --------------------- | ----------------- | -------------------------------------------- |
| Alpha Vantage（選填） | 美股基本面資料    | https://www.alphavantage.co/support/#api-key |
| FinMind（選填）       | 台股資料          | https://finmindtrade.com/                    |
| OpenAI / Anthropic 等（選填） | 雲端 LLM 替代方案 | 各平台申請                           |

### 安裝步驟

#### 1️⃣ 克隆專案

```bash
git clone https://github.com/MarkLo127/TradingAgentsX.git
cd TradingAgentsX
```

#### 2️⃣ 啟動 Ollama 並下載模型

```bash
# 確認 Ollama 已安裝並執行
ollama serve          # 若尚未在背景執行

# 下載預設模型（約 9 GB，首次需要）
ollama pull qwen2.5:14b
```

#### 3️⃣ 後端設置

```bash
# 建立虛擬環境並安裝所有相依套件（使用 uv）
uv sync
uv pip install -e .
uv pip install -r backend/requirements.txt

# 安裝 Shioaji（即時交易功能，選用）
uv run python -m pip install shioaji   # uv run 確保使用正確虛擬環境

# 啟用虛擬環境
source .venv/bin/activate

# 配置環境變數
cp .env.example .env
# 編輯 .env（Ollama 模式不需要 LLM API 金鑰）

# 啟動後端
python -m backend
```

後端服務：

- API: http://localhost:8000
- Swagger 文檔: http://localhost:8000/docs

#### 即時交易 API 測試（需要永豐證券帳號）

```bash
# 連線（simulation=true 為紙上交易，預設開啟）
curl -s -X POST http://localhost:8000/api/trading/connect \
  -H "Content-Type: application/json" \
  -d '{"api_key":"YOUR_KEY","secret_key":"YOUR_SECRET","simulation":true}' \
  | python -m json.tool

# 儲存回傳的 session_id
SESSION="paste-session-id-here"

# 即時報價（台股代碼，如台積電 2330）
curl -s "http://localhost:8000/api/trading/quote/2330?session_id=$SESSION" | python -m json.tool

# 帳戶餘額
curl -s "http://localhost:8000/api/trading/balance?session_id=$SESSION" | python -m json.tool

# 持倉查詢
curl -s "http://localhost:8000/api/trading/positions?session_id=$SESSION" | python -m json.tool

# 模擬下單（BUY 1 張 2330 @ 900 TWD）
curl -s -X POST http://localhost:8000/api/trading/order \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"ticker\":\"2330\",\"action\":\"BUY\",\"price\":900.0,\"quantity\":1}" \
  | python -m json.tool

# 今日委託清單
curl -s "http://localhost:8000/api/trading/orders?session_id=$SESSION" | python -m json.tool

# 斷線
curl -s -X DELETE "http://localhost:8000/api/trading/connect/$SESSION"
```

也可透過 Web UI 操作：啟動前端後前往 `http://localhost:3000/trading`，點選導覽列「Trading / 即時交易」。

#### Shioaji Pro Terminal 設置（選用）

整合 [shioaji-pro-app](https://github.com/Sinotrade/shioaji-pro-app) 全功能交易終端，需額外設置 sidecar binary：

```bash
# 1. 克隆 shioaji-pro-app（在專案根目錄下）
git clone https://github.com/Sinotrade/shioaji-pro-app.git

# 2. 安裝前端依賴
cd shioaji-pro-app
npm install --legacy-peer-deps

# 3. 下載 sidecar binary（Linux x86_64，以 v1.5.5 為例）
mkdir -p src-tauri/binaries
wget https://github.com/Sinotrade/shioaji-pro-app/releases/download/v1.5.5/shioaji-x86_64-unknown-linux-gnu \
  -O src-tauri/binaries/shioaji-x86_64-unknown-linux-gnu
chmod +x src-tauri/binaries/shioaji-x86_64-unknown-linux-gnu
```

設置完成後，`start.sh` 會自動啟動 shioaji-pro-app（port 5173）。在 `/trading` 頁面輸入永豐證券憑證，點選「Start Pro Terminal Server」→「Open Pro Terminal」即可開啟完整交易介面。

> **注意**：sidecar binary 和 `shioaji-pro-app/` 目錄已加入 `.gitignore`，不會被提交至版本控制。每位使用者需自行下載 binary。

#### 4️⃣ 前端設置

```bash
# 安裝依賴（從專案根目錄執行）
bun install --cwd frontend

# 啟動開發伺服器
bun run --cwd frontend dev
```

前端應用: http://localhost:3000

#### 5️⃣ 終端機介面（TUI，選用）

除了 Web 介面，也可以直接在終端機中執行分析。TUI 以 [Textual](https://github.com/Textualize/textual) 打造，`uv pip install -e .` 會一併安裝。

```bash
# 確保已完成後端設置並啟用虛擬環境
source .venv/bin/activate

# 啟動 TUI
python -m tui.main
```

- 於設定畫面選擇市場、股票代碼、分析師團隊、LLM 與嵌入模型；API 金鑰可留空改用 `.env` 中的設定
- 按「開始分析」後，即時顯示各代理進度、訊息與工具呼叫、以及當前報告
- 完成後顯示最終決策（買入 / 賣出 / 持有）；按 `q` 離開

#### 6️⃣ Ubuntu 桌面捷徑（選用）

一鍵啟動腳本 `start.sh` 會自動啟動後端、前端並開啟瀏覽器，可搭配桌面圖示使用：

```bash
# 確認腳本有執行權限（git clone 後應已設定）
chmod +x ~/TradingAgentsX/start.sh

# 建立桌面捷徑
cat > ~/Desktop/TradingAgentsX.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=TradingAgentsX
Comment=Multi-Agent LLM Trading Analysis Platform
Exec=bash -c '/home/tparng/TradingAgentsX/start.sh > /tmp/tradingagentsx-launch.log 2>&1'
Icon=/home/tparng/TradingAgentsX/frontend/public/icon-192-v8.png
Terminal=false
Categories=Finance;
StartupNotify=true
EOF
chmod +x ~/Desktop/TradingAgentsX.desktop
gio set ~/Desktop/TradingAgentsX.desktop metadata::trusted true
```

雙擊桌面圖示即可啟動。若顯示「未受信任」，右鍵 → **Allow Launching**。啟動日誌：`/tmp/tradingagentsx-backend.log`、`/tmp/tradingagentsx-frontend.log`、`/tmp/tradingagentsx-shioaji-app.log`。

---

## 🐳 Docker 部署

```bash
# 配置環境變數
cp .env.example .env

# 啟動服務
docker compose up -d --build

# 查看日誌
docker compose logs -f

# 停止服務
docker compose down -v
```

服務端口：

- 後端: http://localhost:8000
- 前端: http://localhost:3000

---

## 🔒 安全特性

### 本地開發 vs 生產環境

| 功能         | 本地開發 (localhost) | 生產環境 (Railway 等) |
| ------------ | -------------------- | --------------------- |
| Google 登入  | 選用（可不設定）     | 建議啟用              |
| 資料自動清除 | ❌ 不會清除          | ✅ 未登入時離開會清除 |
| PostgreSQL   | 選用                 | 必需                  |
| API 設定儲存 | 永久保留             | 登入後雲端同步        |
| 歷史報告儲存 | 永久保留             | 登入後雲端同步        |

### 前端安全

- **API Key 加密儲存** - 使用 AES-GCM 加密 localStorage 中的敏感資料
- **自動清除（僅生產環境）** - 未登入用戶離開頁面時自動清除本地資料
- **Safari 觸控優化** - 修復 iOS Safari 的觸控事件問題

### 後端安全

- **Rate Limiting** - 每分鐘 30 次請求限制
- **Security Headers** - X-Content-Type-Options、X-Frame-Options 等
- **敏感資料遮罩** - API Key 在日誌中自動遮罩
- **CORS 配置** - 限制跨域請求來源

### 雲端同步

- **Google OAuth 2.0** - 安全的第三方登入
- **JWT Token** - 無狀態認證
- **雲端備份** - API 設定與歷史報告同步到伺服器

---

## 📱 使用指南

### 1. 配置 API 金鑰

點擊右上角「設定」按鈕，輸入您的 API 金鑰。

### 2. 選擇分析參數

- **市場類型**: 美股 / 台股上市 / 台股上櫃
- **股票代碼**: 如 NVDA、2330
- **分析師團隊**: 選擇需要的分析師
- **研究深度**: 淺層（快速）/ 中等 / 深層（詳細）
- **LLM 模型**: 快速思維模型 + 深層思維模型

### 3. 執行分析

點擊「執行分析」，等待 1-5 分鐘（依研究深度而定）。

### 4. 查看結果

- **交易決策摘要** - BUY / SELL / HOLD 建議
- **股價走勢圖** - 折線圖 / K 線圖切換
- **12 位代理報告** - 點擊標籤查看詳細分析

### 5. 儲存與下載

- **儲存報告** - 保存到本地 / 雲端
- **下載 PDF 報告** - 匯出完整 PDF 分析報告

### 📄 範例報告

查看完整的 PDF 分析報告範例：

📥 **[AVGO 博通公司分析報告 (2026-03-21)](report/zh_tw/AVGO_Report_2026-03-21.pdf)**

---

## 🔌 API 文檔

### 健康檢查

```bash
GET /api/health
```

### 執行分析

```bash
POST /api/analyze
Content-Type: application/json

{
  "ticker": "NVDA",
  "market_type": "us",
  "analysis_date": "2024-01-15",
  "research_depth": 2,
  "analysts": ["market", "social", "news", "fundamentals"],
  "quick_think_llm": "qwen2.5:14b",
  "deep_think_llm": "qwen2.5:14b",
  "quick_think_base_url": "http://localhost:11434/v1",
  "deep_think_base_url": "http://localhost:11434/v1",
  "quick_think_api_key": "ollama",
  "deep_think_api_key": "ollama",
  "alpha_vantage_api_key": "..."
}
```

> 使用雲端 LLM（如 OpenAI、Anthropic）時，將 `quick_think_llm`/`deep_think_llm` 替換為對應模型名稱，並填入真實的 API 金鑰與 Base URL。

### 查詢任務狀態

```bash
GET /api/task/{task_id}
```

完整文檔: http://localhost:8000/docs

---

## 🛠️ 技術棧

### 後端

| 技術                 | 用途                              |
| -------------------- | --------------------------------- |
| FastAPI              | 異步 Web 框架                     |
| LangGraph            | 多代理工作流編排                  |
| LangChain            | LLM 應用開發                      |
| Ollama               | 本地 LLM 推理（預設 qwen2.5:14b） |
| ChromaDB             | 向量資料庫（記憶系統）            |
| PostgreSQL           | 使用者資料儲存                    |
| SQLAlchemy + asyncpg | 異步資料庫 ORM                    |
| Pydantic             | 資料驗證                          |
| uv                   | Python 套件管理                   |

### 前端

| 技術         | 用途           |
| ------------ | -------------- |
| Next.js 16   | React 全端框架 |
| TypeScript   | 靜態型別       |
| Tailwind CSS | 樣式框架       |
| shadcn/ui    | UI 組件庫      |
| Dexie.js     | IndexedDB 封裝 |
| Recharts     | 資料視覺化     |

---

## 📸 應用截圖

### 首頁

![首頁](web_screenshot/1.png)

---

### API 配置頁面

![API配置頁面](web_screenshot/2.png)

---

### 任務配置頁面

![任務配置頁面](web_screenshot/3.png)

---
### 分析歷史

![分析歷史](web_screenshot/4.png)

---

### 12位分析師報告

![12位分析師報告](web_screenshot/5.png)
![12位分析師報告](web_screenshot/5_1.png)

---

### PDF報告預覽與下載

![PDF報告預覽與下載](web_screenshot/6.png)

---

### 報告AI問答

![報告AI問答](web_screenshot/7.png)

---

## 🙏 致謝

- [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) - 原始專案
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 應用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 多代理編排
- [FastAPI](https://github.com/tiangolo/fastapi) - Web 框架
- [Next.js](https://github.com/vercel/next.js) - React 框架
- [shadcn/ui](https://github.com/shadcn/ui) - UI 組件庫

---

## 📄 License

本專案採用 Apache 2.0 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。
