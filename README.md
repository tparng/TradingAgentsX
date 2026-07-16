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
| 📋 **自選股清單**        | 追蹤股票、同步 Google Sheets、Telegram 通知、APScheduler 定時自動分析          |
| 🔍 **候選股篩選**        | 規則篩選（漲幅 + 量比）＋ LLM 評分排名，UI 選取後一鍵加入自選股              |
| 🌏 **美股/台股切換**     | 自選股與候選股均支援市場切換，一鍵分別檢視美股與台股清單                      |
| 🔡 **字體大小調整**      | 頁首提供 Small / Medium / Large / X-Large 四段字體大小選擇，設定自動保存       |

---

## 🔧 近期變更

### v8 改進（當前版本）

| 變更項目 | 說明 |
| -------- | ---- |
| **候選股篩選器（Screener）** | 新增 `screener_service.py`：對美股（65 支）與台股（32 支）Universe 進行規則篩選（`min_price_change_pct`、`min_volume_ratio`）與綜合評分（`price_change_weight`），取 Top-N 傳遞給 LLM |
| **LLM 候選股排名（Candidate Service）** | 新增 `candidate_service.py`：`rank_candidates()` 呼叫本地 Ollama（或任意 LLM）對篩選結果評分排名並輸出信號（BUY/SELL/NEUTRAL）與理由；`generate_detail_report()` 按需（懶載入）生成完整 7 段 Markdown 分析報告，支援中英文切換 |
| **候選股 REST API** | `POST /api/watchlist/candidates/generate`（執行篩選 + LLM 排名，接受 `ScreenerParams` 參數體）、`GET /api/watchlist/candidates`（列出 pending 候選股）、`POST /api/watchlist/candidates/add`（批量加入自選股）、`GET /api/watchlist/candidates/{ticker}/detail`（按需生成詳細報告）、`DELETE /api/watchlist/candidates/{ticker}`（忽略候選股）|
| **WatchlistCandidate 資料模型** | `backend/app/db/models.py` 新增 `WatchlistCandidate`：ticker（唯一索引）、market_type、price_change_pct、volume_ratio、rsi、rationale、rank、signal、screened_at、status（pending/added/dismissed）|
| **候選股 UI 面板** | 自選股頁面新增候選股區塊：「Generate Candidates」按鈕觸發篩選；複選框選取後批量加入；點擊候選股卡片開啟 Dialog，顯示當前價、30日高低、RSI 等指標，並以 ReactMarkdown 渲染按需生成的 AI 詳細分析報告 |
| **篩選器參數調整 UI** | 候選股面板新增可展開的 ScreenerSettingsPanel：滑桿調整最小漲幅（0.5–10%）、最小量比（1.0–5.0×）、漲幅/量比權重（即時顯示比例）、篩選上限（5–50）、LLM 評選上限（3–15）；US/TW 宇宙 Switch；「Reset」一鍵還原預設值 |
| **「Full Analysis」預填 ticker** | 候選股詳細報告 Dialog 新增「Full Analysis」按鈕，開啟 `/analysis?ticker=XXX&market_type=us`；`AnalysisForm` 新增 `initialTicker`/`initialMarketType` props；`app/analysis/page.tsx` 以 `useSearchParams` 讀取並預填表單；以 `<Suspense>` 包裹解決 Next.js App Router 靜態渲染問題 |
| **美股 / 台股市場切換** | 自選股頁面頁首新增 US / TWN 雙鍵切換，自選股清單與候選股均以市場類型做 Client 端過濾（無需後端改動）；切換時自動更新「Generate」篩選範圍，並顯示各市場筆數角標 |
| **修復 429 Rate Limit 錯誤** | `RateLimitMiddleware` 改為僅對 POST/PUT/DELETE 計次，GET 請求全部豁免（自選股頁面一次觸發 3 個 GET）；預設上限從 30 提升至 60 次/分鐘；新增 `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` 環境變數支援動態調整 |
| **字體大小選擇器** | 新增 `FontSizeContext`（localStorage 持久化）及 `FontSizeToggle` 組件；頁首（桌面版與行動版）新增字體大小圖示（`ALargeSmall`），下拉選單提供 Small（13px）/ Medium（16px）/ Large（18px）/ X-Large（20px）四段選擇；透過 `html[data-font-size]` CSS 屬性全局縮放所有 rem 尺寸 |

### v7 改進

| 變更項目 | 說明 |
| -------- | ---- |
| **自選股清單頁面** | 新增 `/watchlist` 頁面：新增/移除股票代碼、查看最後分析結果（決策/評分）、一鍵觸發分析或跳轉分析頁 |
| **Google Sheets 雙向同步** | 以 GCP 服務帳戶（`GOOGLE_SERVICE_ACCOUNT_JSON`）連接指定試算表（`GOOGLE_SHEET_ID`）；新增時同步寫入 Sheet，分析完成後自動更新 Last Analyzed / Recommendation / Score 欄位；支援現有 Sheet 格式（公司名稱欄自動識別、市場類型自動偵測：純數字→ twse，英文字母→ us） |
| **Telegram Bot 通知** | 分析完成時推送個股結果（決策 + 評分）；支援每日摘要（所有自選股一覽）；分析失敗時推送錯誤訊息；以 httpx 直接呼叫 Bot API，無需 python-telegram-bot 套件 |
| **APScheduler 排程器** | 內嵌於 FastAPI 行程（`AsyncIOScheduler`）；每 15 分鐘自動從 Sheet 同步自選股清單；支援自定義 Cron 排程（`WATCHLIST_ANALYSIS_CRON`，如 `0 9 * * 1-5`）定時分析全部自選股 |
| **自選股 REST API** | `GET/POST/DELETE /api/watchlist`（CRUD）、`POST /api/watchlist/sync`（手動 Sheet 同步）、`POST /api/watchlist/analyze`（觸發分析，支援全部或單一標的）、`GET /api/watchlist/status`（排程器與服務狀態）|
| **PostgreSQL 本地設置** | 新增 `DATABASE_URL` 至 `.env`；修復 uvicorn reload 子行程未載入 `.env` 的問題（在 `backend/app/main.py` 頂部呼叫 `load_dotenv()`，確保 `asyncpg` 引擎在子行程中也能讀取環境變數） |
| **新增套件** | `apscheduler>=3.10.4`、`gspread>=6.0.0`、`google-auth>=2.0.0`、`asyncpg`（補裝）加入 `backend/requirements.txt` |
| **修正模型名稱** | 排程器 LLM 預設從 `qwen2.5:14b` 修正為 `qwen2.5:14b-16k`，與其他頁面保持一致 |

### v6 改進

| 變更項目 | 說明 |
| -------- | ---- |
| **預設模型改為 qwen2.5:14b-16k** | 將預設 LLM 從 `qwen2.5:14b-32k`（32768 token）改為 `qwen2.5:14b-16k`（16384 token）；16k context 的 KV cache 僅需 3 GB（32k 需 6 GB），使模型總記憶體需求（約 11.5 GB）可完整放入 RTX 3080 Ti（16 GB VRAM），避免退回 CPU 推理 |
| **新增 Modelfile.qwen2.5-14b-16k** | 以 `ollama create qwen2.5:14b-16k -f Modelfile.qwen2.5-14b-16k` 建立本地 16k context 模型，不需重新下載權重（從 `qwen2.5:14b` 衍生） |
| **分析表單預設更新** | 分析頁面快速/深層模型預設改為 `custom` + `qwen2.5:14b-16k` |
| **shioaji 加入正式依賴** | `pyproject.toml` 新增 `shioaji>=1.5.6`，`uv sync` 後即可使用即時交易功能 |
| **Ollama GPU 修復（升級至 v0.32.0）** | v0.23.1 存在 GPU 偵測 bug：bootstrap probe（`--ollama-engine`）回傳 `initial_count=0`，導致 model runner 不帶 `--num-gpu` 旗標，全程使用 CPU 推理（797% CPU、5–8 分鐘/次呼叫）；升級至 v0.32.0 後 GPU 正常偵測。**升級指令**：`curl -fsSL https://ollama.com/install.sh \| sudo sh` |
| **Ollama 建議以手動方式啟動** | 安裝腳本建立的 systemd service 以 `User=ollama` 執行，無法存取 `/home/tparng/data/ollama/models`；建議停用 systemd service（`sudo systemctl disable --now ollama`）並以使用者身分手動啟動：`OLLAMA_MODELS=/home/tparng/data/ollama/models OLLAMA_NUM_CTX=16384 nohup ollama serve > /tmp/ollama.log 2>&1 &` |
| **CUDA vs Vulkan 說明** | v0.32.0 升級後若出現 `cuInit failed: 999`（CUDA_ERROR_UNKNOWN），Ollama 會自動回退至 Vulkan GPU 加速（仍比 CPU 快數倍）；`cuInit: 999` 通常發生在驅動程式庫更新後尚未重開機，**重開機後 CUDA 即可正常使用** |
| **tokenizers 版本修復** | `sentence-transformers` 需要 `tokenizers>=0.22.0`；若遇到匯入錯誤，執行 `uv pip install "tokenizers>=0.22.0" transformers -U` |

### v5 改進

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
| **整合 Shioaji Pro Terminal** | 整合 [shioaji-pro-app](https://github.com/Sinotrade/shioaji-pro-app) 全功能交易終端（AGPL-3.0）；後端以 `ShioajiServerManager` 管理 sidecar binary（port 21322），新增 `/api/shioaji-server/{start,stop,status}` 3 個端點；`/trading` 頁面新增「Shioaji Pro Terminal」卡片，一鍵啟動伺服器並在新分頁開啟完整交易介面 |
| **修復 Sidecar 啟動方式** | Sidecar binary 不接受 `--api-key` / `--secret-key` / `--port` CLI 參數；改以環境變數傳入（`SJ_API_KEY`、`SJ_SEC_KEY`、`SJ_HTTP_ADDR`、`SJ_PRODUCTION`），指令改為 `server start --no-open` |
| **修復交易頁 Hydration 錯誤** | `sessionId` 改為從 `null` 初始化，並在 `useEffect` 中從 localStorage 還原，解決 SSR/Client HTML 不符問題；`hasSavedCreds` 替代 `typeof window !== "undefined"` 判斷；連線憑證表單移至獨立常駐卡片，不再被 `!isConnected` 隱藏 |
| **Sidecar 內建 UI** | 發現 sidecar binary 已內建完整 Web 介面（`http://localhost:21322/`），「Open Pro Terminal」改為直接開啟 port 21322，無需另啟 shioaji-pro-app 開發伺服器 |
| **Sidecar 啟動逾時 & 錯誤優化** | 健康輪詢從 10 s 延長至 60 s（載入 ~5 萬張合約需 20–40 s）；錯誤訊息截取上限從 500 字元增至 2000 字元並移除 ANSI 色碼 |
| **修復 Port 衝突** | 啟動前先偵測 port 21322 是否已有健康 sidecar（採用既有 process），或以 `fuser` 清除殭屍 process 再啟動，避免 `EADDRINUSE` 錯誤 |
| **Sidecar 正式模式 CA 憑證支援** | 新增 CA 憑證欄位（Sinopac.pfx 路徑、憑證密碼）；以 `SJ_CA_PATH` / `SJ_CA_PASSWD` 環境變數傳入 sidecar；切換 Simulation 關閉並設定 CA 路徑後，正式環境下單憑證自動啟用 |
| **修正 Pro Terminal 開啟目標** | Port 21322 為 sidecar REST API 管理儀表板（Server Health、CA Certificates 等系統資訊），全功能交易介面（圖表、自選股、下單表單）為 shioaji-pro-app 前端（port 5173，由 `start.sh` 啟動）；「Open Pro Terminal」改回開啟 port 5173，並在卡片新增管理儀表板捷徑連結 |
| **Sidecar stdout 即時擷取 & 停機診斷** | 後端以背景執行緒持續讀取 sidecar stdout，保留最後 50 行；`GET /api/shioaji-server/status` 新增 `last_output` 欄位；前端健康輪詢（每 10 s）偵測到伺服器意外停止時，自動顯示最後 10 行輸出協助診斷 |
| **CA 啟動失敗即時警示** | sidecar 啟動成功後，後端掃描 stdout 比對 `"Failed to activate CA certificate:"` 模式；若 CA 啟動失敗（憑證過期、密碼錯誤），回傳 `ca_warning`；前端以黃色警示顯示失敗原因（「正式環境下單將被拒絕」） |
| **修復模式切換未重啟問題** | 追蹤 `runningSimulation` 狀態，記錄 sidecar 實際啟動的模式；切換 Simulation 切換鈕時若與執行中 sidecar 模式不一致，顯示黃色警示並提供「Restart」一鍵重啟按鈕，確保模式變更實際生效 |
| **CA 密碼持久化** | CA 憑證密碼現以 AES-256-GCM 加密存入 localStorage（與 API Key 一致），頁面重載後自動預填；先前每次重啟均需重新輸入密碼，導致 sidecar 以空密碼啟動而靜默失敗 CA 啟用 |
| **帳號簽署後須重啟 sidecar** | 在永豐 API 管理頁簽署 API 約定書後，sidecar 需重啟才能讀取更新的 `signed: true` 狀態；簽署前 sidecar 快取的帳號資訊仍為 `signed: false`，導致 Portfolio / Order 端點回傳 406 |
| **帳號類型說明** | shioaji 僅支援 `S`（證券）與 `F`（期貨）兩種帳號類型；永豐可能回傳 `H`（Sinopac 內部類型，如海外證券）等額外類型，shioaji-pro-app 會略過 `S`/`F` 以外的帳號，Margin 等功能亦不適用 |

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
| **預設 LLM 切換為 Ollama** | 預設使用 `qwen2.5:14b-16k`（本地推理，16384 token 上下文），無需 OpenAI API 金鑰（v6 起從 32k 改為 16k 以確保 GPU 加速） |
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
| `tradingagents/default_config.py` | 修改 | 預設 LLM 改為 Ollama/qwen2.5:14b-16k（16384 token 上下文，v6 從 32k 改為 16k 以啟用 GPU 加速）；新聞來源改為 Google News RSS（無需 API 金鑰）；全域新聞改為 local/Reddit |
| `tradingagents/dataflows/interface.py` | 修改 | 所有中文除錯輸出改為英文 `[vendor]` 格式；錯誤訊息英文化 |
| `tradingagents/dataflows/local.py` | 修改 | 頂層 `import polars` 改為 `try/except ImportError`，避免未安裝 polars 時後端啟動崩潰 |
| `tradingagents/dataflows/alpha_vantage_common.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/stockstats_utils.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/utils.py` | 修改 | 同上，防護性 polars 匯入 |
| `tradingagents/dataflows/yfin_utils.py` | 修改 | 同上，防護性 polars 匯入 |

### 後端

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `backend/app/services/sheets_service.py` | **新增** | `SheetsService`：以 GCP 服務帳戶連接試算表；`get_tickers_from_sheet()`（自動偵測市場類型）、`add/remove_ticker_from_sheet()`、`write_analysis_result()`（更新 Last Analyzed / Recommendation / Score 欄） |
| `backend/app/services/telegram_service.py` | **新增** | `TelegramService`：透過 httpx 呼叫 Bot API；`send_analysis_complete()`、`send_daily_digest()`、`send_error()` |
| `backend/app/services/scheduler_service.py` | **新增** | `WatchlistScheduler`（`AsyncIOScheduler`）：`sheet_sync` job（每 15 分鐘）+ `daily_analysis` job（CRON 排程）；`run_watchlist_analysis()` 可依 ticker 清單或全部執行 |
| `backend/app/services/screener_service.py` | **新增** | 規則篩選引擎：美股（65 支）/ 台股（32 支）Universe；`run_screener()` 以 asyncio.gather 並發篩選兩個市場；`get_ticker_detail()` 取得 30 日價格區間、RSI、量比；`_score_ticker()` 計算綜合評分 |
| `backend/app/services/candidate_service.py` | **新增** | LLM 評分層：`rank_candidates()` 呼叫 Ollama 排名篩選結果並輸出 JSON 信號；`generate_detail_report()` 按需生成完整 7 段 Markdown 報告（支援中英文）；`_parse_llm_response()` 解析並驗證 LLM 輸出 |
| `backend/app/api/watchlist_routes.py` | **新增/修改** | 原有 `GET/POST/DELETE /api/watchlist`、`/sync`、`/analyze`、`/status`；v8 新增候選股 5 個端點：`POST /candidates/generate`（`ScreenerParams` 參數體）、`GET /candidates`、`POST /candidates/add`（批量）、`GET /candidates/{ticker}/detail`（按需報告）、`DELETE /candidates/{ticker}`（忽略）；新增 `ScreenerParams`、`CandidateOut`、`BulkAddRequest` Pydantic 模型 |
| `backend/app/db/models.py` | 修改 | 新增 `WatchlistItem` 模型（ticker、market_type、notes、added_at、last_analyzed_at、last_recommendation、last_score）；單一擁有者設計，無 user_id；v8 新增 `WatchlistCandidate` 模型（ticker 唯一索引、signal、rationale、rank、screened_at、status） |
| `backend/app/db/database.py` | 修改 | `init_db()` 新增 watchlist 資料表欄位 migration |
| `backend/app/core/config.py` | 修改 | 新增 Telegram、Google Sheets、watchlist 排程器相關環境變數欄位 |
| `backend/app/main.py` | 修改 | 頂部呼叫 `load_dotenv()` 修復 uvicorn reload 子行程讀不到 `.env` 的問題；新增 `watchlist_router`；startup/shutdown 事件啟動/停止排程器；v8：`RateLimitMiddleware` 豁免所有 GET 請求，預設限制提升至 60/min，新增 `RATE_LIMIT_MAX_REQUESTS`/`RATE_LIMIT_WINDOW_SECONDS` 環境變數 |
| `backend/__main__.py` | 修改 | 頂部呼叫 `load_dotenv()` 確保主行程也能讀取 `.env` |
| `backend/requirements.txt` | 修改 | 新增 `apscheduler>=3.10.4`、`gspread>=6.0.0`、`google-auth>=2.0.0` |
| `.env.example` | 修改 | 新增 `DATABASE_URL`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`、`GOOGLE_SERVICE_ACCOUNT_JSON`、`GOOGLE_SHEET_ID`、`WATCHLIST_*` 相關環境變數 |
| `backend/app/models/schemas.py` | 修改 | `AnalysisRequest` 新增 `language` 欄位，接收前端傳入的報告語言設定 |
| `backend/app/services/trading_service.py` | 修改 | 將 `language` 傳入 `TradingAgentsXGraph` 設定；結果字典新增 `quant_report` |
| `backend/app/services/shioaji_service.py` | **新增** | `ShioajiSessionManager` 單例：以 UUID 管理 Shioaji 連線（8 小時 TTL、threading.Lock），封裝報價、餘額、持倉、下單、取消委託等操作 |
| `backend/app/api/trading_routes.py` | **新增** | 8 個 `/api/trading/*` REST 端點，以 `asyncio.to_thread()` 包裝阻塞式 Shioaji 呼叫以相容 FastAPI 非同步環境 |
| `backend/app/services/shioaji_server_service.py` | **新增** | `ShioajiServerManager` 單例：管理 sidecar binary 生命週期；憑證以環境變數傳入（含 `SJ_CA_PATH`/`SJ_CA_PASSWD`）；健康輪詢 60 s；背景執行緒持續讀取 stdout（最後 50 行）；啟動成功後掃描 CA 啟動失敗模式；啟動前偵測既有健康 process 或以 `fuser` 清除殭屍 process；錯誤訊息去除 ANSI 色碼 |
| `backend/app/api/shioaji_server_routes.py` | **新增** | 3 個 `/api/shioaji-server/*` REST 端點：`POST /start`（啟動 sidecar，含 `ca_path`/`ca_passwd`/`ca_warning` 回傳）、`POST /stop`（停止）、`GET /status`（回傳 running/healthy/pid/last_output） |
| `backend/app/main.py` | 修改 | 匯入並註冊 `trading_router` 及 `shioaji_server_router` |

### 前端

| 檔案 | 變更類型 | 原因 |
| ---- | -------- | ---- |
| `frontend/app/watchlist/page.tsx` | **新增/修改** | v7：自選股清單頁面（CRUD、Sync、Analyze、狀態列）；v8：新增候選股面板（Generate 按鈕、篩選器設定 Panel、候選股卡片複選）、`CandidateDetailModal`（Dialog + ReactMarkdown 詳細報告、指標列、Dismiss/Full Analysis/Add 按鈕）、美股/台股市場切換頁首按鈕、Client 端市場過濾邏輯 |
| `frontend/lib/types.ts` | 修改 | 新增 `WatchlistItem`、`WatchlistStatus`；v8 新增 `WatchlistCandidate`、`CandidateDetail`、`ScreenerParams` 介面及 `DEFAULT_SCREENER_PARAMS` 常數 |
| `frontend/lib/api.ts` | 修改 | 新增 `getWatchlist`、`addToWatchlist`、`removeFromWatchlist`、`syncWatchlistFromSheet`、`triggerWatchlistAnalysis`、`getWatchlistStatus`；v8 新增 `getCandidates`、`generateCandidates`、`addCandidatesToWatchlist`、`dismissCandidate`、`getCandidateDetail`（120s 逾時）|
| `frontend/contexts/FontSizeContext.tsx` | **新增** | `FontSizeProvider`：將字體大小偏好以 `data-font-size` 屬性設於 `<html>` 元素，並持久化至 localStorage；`useFontSize()` Hook |
| `frontend/components/theme/FontSizeToggle.tsx` | **新增** | 下拉選單組件（`ALargeSmall` 圖示）：Small / Medium / Large / X-Large 四段字體大小選擇，支援中英文標籤，當前選項高亮 |
| `frontend/components/analysis/AnalysisForm.tsx` | 修改 | 新增 `initialTicker`/`initialMarketType` props，讓候選股「Full Analysis」按鈕可預填 ticker 與市場類型 |
| `frontend/app/analysis/page.tsx` | 修改 | 以 `useSearchParams` 讀取 `?ticker=` 與 `?market_type=` URL 參數並傳入 `AnalysisForm`；以 `<Suspense>` 包裹解決 App Router 靜態渲染限制 |
| `frontend/app/layout.tsx` | 修改 | 在 Provider 樹中加入 `<FontSizeProvider>` |
| `frontend/components/layout/Header.tsx` | 修改 | 桌面版與手機版導覽列新增「Watchlist / 自選股」連結；v8 新增 `<FontSizeToggle />`（位於語言切換器與主題切換器之間）|
| `frontend/app/globals.css` | 修改 | 新增 `html[data-font-size="sm|md|lg|xl"]` CSS 規則（13/16/18/20px），全局縮放所有 rem 尺寸 |
| `frontend/lib/i18n/en.ts` | 修改 | 新增 `nav.watchlist` 及 `watchlist` 區段（30+ 鍵）英文 i18n 字串；v8 新增 `watchlist.marketSwitch`、`watchlist.candidates.settings`、`watchlist.candidates.detail` 等候選股相關字串 |
| `frontend/lib/i18n/zh-TW.ts` | 修改 | 新增 `nav.watchlist`（自選股）及 `watchlist` 區段繁體中文 i18n 字串；v8 新增候選股相關繁體中文字串 |
| `frontend/app/trading/page.tsx` | 修改 | 新增「Shioaji Pro Terminal」卡片：呼叫 `/api/shioaji-server/start` 啟動 sidecar；就緒後「Open Pro Terminal」在新分頁開啟 `localhost:5173`（shioaji-pro-app 全功能交易介面）；憑證表單移至獨立常駐卡片（修復 hydration 錯誤及憑證被 `!isConnected` 隱藏的問題）；新增 CA 憑證欄位；`runningSimulation` 追蹤執行中模式並在模式不一致時顯示 Restart 警示；CA 密碼加密存入 localStorage；`ca_warning` 以黃色警示顯示；停機時顯示 sidecar 最後輸出；卡片附管理儀表板連結（port 21322）；保留簡易交易四分頁 |
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
│   │   ├── watchlist/          # 自選股清單頁面
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
│   ├── contexts/               # React Context（認證、語言、字體大小）
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
│       │   ├── watchlist_routes.py     # 自選股 CRUD + 觸發 API
│       │   └── dependencies.py # 依賴注入
│       ├── core/               # 核心配置
│       ├── db/                 # PostgreSQL 資料庫（含 WatchlistItem 模型）
│       ├── models/             # Pydantic 模型
│       └── services/           # 業務邏輯
│           ├── trading_service.py      # 交易分析服務
│           ├── shioaji_service.py      # Shioaji Python lib session 管理
│           ├── shioaji_server_service.py # Sidecar binary 生命週期管理
│           ├── screener_service.py     # 候選股規則篩選（漲幅 + 量比 + RSI）
│           ├── candidate_service.py    # LLM 評分排名 + 詳細報告生成
│           ├── sheets_service.py       # Google Sheets 雙向同步（gspread）
│           ├── telegram_service.py     # Telegram Bot 推播通知（httpx）
│           ├── scheduler_service.py    # APScheduler：Sheet 同步 + 定時分析
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
| Telegram Bot（選填）  | 自選股分析通知    | 向 @BotFather 建立 Bot，以 @userinfobot 取得 Chat ID |
| GCP 服務帳戶（選填）  | Google Sheets 同步 | GCP Console → IAM → 服務帳戶，賦予試算表編輯權限 |

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

# 下載模型（約 9 GB，首次需要）
ollama pull qwen2.5:14b

# 建立 16k context 版本（推薦：可完整放入 16 GB VRAM，啟用 GPU 加速）
ollama create qwen2.5:14b-16k -f Modelfile.qwen2.5-14b-16k
# 或手動建立：
# ollama create qwen2.5:14b-16k -f - <<'EOF'
# FROM qwen2.5:14b
# PARAMETER num_ctx 16384
# EOF
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

> **帳號簽署**：Portfolio / Order 功能需先至[永豐 API 管理頁](https://www.sinotrade.com.tw/ec/20210518/index.html)簽署 API 約定書（帳號 `signed: true`）。簽署後須重啟 sidecar（在 `/trading` 頁面點選 Stop → Start）才能生效。shioaji 僅支援 `S`（證券）與 `F`（期貨）帳號，`H` 等其他類型會被略過。

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

- **Rate Limiting** - 預設每分鐘 60 次請求限制（僅對 POST/PUT/DELETE 計次，GET 全部豁免）；可透過 `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` 環境變數調整
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

**Markdown 報告**（由本系統生成，可直接在 GitHub 上閱讀）：

| 股票 | 日期 | 連結 |
| ---- | ---- | ---- |
| NVDA (NVIDIA) | 2026-07-15 | [NVDA_Report_2026-07-15.md](report/NVDA/NVDA_Report_2026-07-15.md) |
| NVDA (NVIDIA) | 2026-07-13 | [NVDA_Report_2026-07-13.md](report/NVDA/NVDA_Report_2026-07-13.md) |
| NVDA (NVIDIA) | 2025-01-10 | [NVDA_Report_2025-01-10.md](report/NVDA/NVDA_Report_2025-01-10.md) |
| 2330 (台積電) | 2026-07-14 | [2330_Report_2026-07-14.md](report/2330/2330_Report_2026-07-14.md) |

> 報告由 `scripts/export_reports_to_md.py` 從 `eval_results/` 自動轉換，執行 `python3 scripts/export_reports_to_md.py` 可更新。

**PDF 報告**：

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
  "quick_think_llm": "qwen2.5:14b-16k",
  "deep_think_llm": "qwen2.5:14b-16k",
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

### 自選股清單

```bash
# 取得清單
GET /api/watchlist

# 新增股票
POST /api/watchlist
{ "ticker": "2330", "market_type": "twse", "notes": "台積電" }

# 移除股票
DELETE /api/watchlist/2330

# 從 Google Sheet 同步
POST /api/watchlist/sync

# 觸發分析（全部或單一）
POST /api/watchlist/analyze
{ "ticker": "NVDA" }   # 省略 ticker 則分析全部自選股

# 排程器與服務狀態
GET /api/watchlist/status
```

### 候選股篩選

```bash
# 執行篩選 + LLM 排名（接受自訂參數）
POST /api/watchlist/candidates/generate
{
  "min_price_change_pct": 1.5,
  "min_volume_ratio": 1.5,
  "price_change_weight": 0.6,
  "include_us": true,
  "include_tw": true,
  "max_screener_candidates": 20,
  "llm_top_n": 8
}

# 取得目前 pending 候選股
GET /api/watchlist/candidates

# 批量加入自選股
POST /api/watchlist/candidates/add
{ "tickers": ["NVDA", "AAPL"] }

# 按需生成詳細 AI 分析報告（約 15–40 秒）
GET /api/watchlist/candidates/{ticker}/detail

# 忽略候選股（標記為 dismissed）
DELETE /api/watchlist/candidates/{ticker}
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
| APScheduler          | 排程器（Sheet 同步 + 定時分析）   |
| gspread + google-auth | Google Sheets 雙向同步           |
| httpx                | Telegram Bot API 推播通知         |

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
