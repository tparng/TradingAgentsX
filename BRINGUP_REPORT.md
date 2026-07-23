# TradingAgentsX — Bring-Up Report

**Period:** 2026-07-16 to 2026-07-23  
**Branch:** `main`  
**Author:** tparng

---

## Features Added

### 1. Cancel Analysis
- Added `cancelAnalysis` i18n key to `en.ts` and `zh-TW.ts`
- Backend `/api/task/{id}/cancel` route and `threading.Event` passed through `trading_service → trading_graph → propagate()` loop
- Frontend `useAnalysis` hook and cancel button wired to task status polling
- Task status type union extended: `"cancelling" | "cancelled"` added to `TaskStatusResponse`

### 2. Progress Timeline — Analyst Filtering
- **Problem:** The live analysis timeline always showed all 14 steps even when only 1 analyst was selected
- **Fix:** `AnalysisProgress.tsx` accepts an `analysts?: string[]` prop; `ANALYST_KEY_TO_NODE` map translates form keys to node labels; `activePipeline` filters out unselected analyst steps before rendering
- Phase headers now track `visibleSteps[idx-1]?.phase` instead of the raw `PIPELINE` array index

### 3. LLM Server Status Indicator
- New component `frontend/components/analysis/LlmStatusIndicator.tsx`
  - Polls `GET /api/llm/status?base_url=...` on mount and every 30 s
  - Debounces URL changes by 600 ms
  - Shows green / red / pulsing-grey dot + label
- Backend `GET /api/llm/status` proxy in `routes.py` — hits `{base_url}/models`, returns `{status: "online"|"offline"}`
- Inserted into `AnalysisForm.tsx` above the LLM settings section, tracking `quick_think_base_url`

### 4. Analysis History — 0-Count Fix
- **Root cause:** `loadReports` and `loadCounts` in `history/page.tsx` filtered reports by UI locale; any language switch after saving made all reports disappear
- **Fix:** Removed all `filterByLang` / `filterByLanguage` calls; `locale` removed from `useEffect` dependency array; all counts now show regardless of current language setting

### 5. Crypto Stability Fix (Pro Terminal OperationError)
- **Root cause:** `getBrowserFingerprint()` in `crypto.ts` used `userAgent`, screen dimensions, and `timezoneOffset` — all of which change across browser updates, resizes, and DST transitions, breaking AES-GCM key derivation
- **Fix:** Replaced fingerprint with a fixed constant `APP_KEY_MATERIAL = "tradingagentsx-secure-storage-v1"`; `decrypt()` now returns `""` instead of throwing on failure so stale entries are silently cleaned up
- The random per-value salt (stored alongside the ciphertext in localStorage) provides equivalent security without the instability

### 6. Trading Page — Persist Credentials
- Shioaji API key, secret key, CA path, CA password, and simulation mode now survive page reloads
- Load effect: if `decrypt()` returns `""` (stale entry), the key is removed from localStorage rather than crashing
- All three save paths (Start, Restart, Connect) write `shioaji_simulation` to localStorage
- "Clear saved credentials" button also clears `shioaji_simulation`

### 7. Watchlist → Pro Terminal Integration
**Open in Pro Terminal button (Taiwan stocks only)**
- `openInProTerminal(ticker)` in `watchlist/page.tsx`
  - Uses `window.open('', 'shioaji-pro-terminal')` probe; detects cross-origin window by catching `SecurityError` on `.document` access
  - If terminal is already open: sends `window.postMessage({ type: 'sj-select-code', code }, 'http://localhost:5173')` and focuses the window
  - If not open: opens `http://localhost:5173/?code={ticker}` in a named window
- `LineChart` icon button added to each TWSE / TPEx watchlist row action cell

**Pro Terminal — receive postMessage (App.tsx, git-ignored)**
- Added `window.addEventListener('message')` handler; routes `sj-select-code` messages to `selectByCodeRef.current(code)`
- Fixed `?code=` URL param handling for the main window: added `initialCodeApplied` ref + `useEffect` so the first symbol comes from the URL param instead of always defaulting to `items[0]`

### 11. Order Flow Analyst — 5th Parallel Analyst in Propagation Phase
- New `tradingagents/agents/analysts/orderflow_analyst.py` — `create_orderflow_analyst(llm, language)` node
- **Taiwan stocks**: calls `get_tick_microstructure` first (VWAP, buy/sell imbalance, block-trade footprint, session momentum), then `get_stock_data` for 30-day OHLCV volume context
- **US stocks**: no tick source; falls back to volume-pattern analysis via `get_stock_data` only (OBV trend, price-volume divergence, accumulation/distribution)
- Full bilingual EN / ZH-TW 5-section report structure: order flow summary → microstructure deep-dive → volume context → trading implication → key metrics table
- `orderflow_report` field added to `AgentState`; `should_continue_orderflow` routing added to `ConditionalLogic`; `"orderflow"` tool node (`get_tick_microstructure` + `get_stock_data`) added to `TradingAgentsXGraph._create_tool_nodes()`; `"Orderflow Analyst"` added to `_PROGRESS_NODES`
- `setup.py` wires the analyst into the sequential chain when `"orderflow"` is in `selected_analysts`
- `trading_service.py` extracts `orderflow_report`; both `ANALYST_MAPPING` blocks in `routes.py` include `"orderflow"` key; `pdf_generator.py` TEAMS and `download_service.py` analyst_order include the new analyst
- Frontend: `orderflow_analyst` i18n keys (EN + ZH-TW), checkbox in `AnalysisForm.tsx`, pipeline entry in `AnalysisProgress.tsx`
- **Clean separation**: tick tool, `is_taiwan` detection, and all `tick_section`/`tick_tool_note` variables removed from `market_analyst.py` — microstructure analysis now exclusively owned by the orderflow analyst

### 10. Tick Microstructure Page in Analysis PDF (Taiwan stocks)
- Raw tick data fetched independently in `trading_service.py` after analysis completes (separate from the LLM text path); stored as `tick_data` in the result dict; threaded through `download_service → pdf_generator`
- New `_generate_tick_chart()` in `pdf_generator.py` — two-panel matplotlib chart:
  - **Top panel:** Intraday price line with dashed VWAP; green fill above VWAP, red fill below
  - **Bottom panel:** Buy vs sell volume as mirrored bars bucketed into ~30 time segments
- New `_build_tick_page()` — dedicated PDF page inserted after the price chart page; includes the chart + a 12-row metrics table (tick count, volume, avg trade size, VWAP, last price, VWAP deviation, buy/sell split, imbalance index, block trade %, session momentum, avg spread)
- i18n labels added to `PDF_LABELS` for both EN and ZH-TW
- Page is silently skipped for US stocks or when sidecar is offline — no error, no empty page

### 9. Intraday Tick Microstructure in Market Analyst (Taiwan stocks)
- New `tradingagents/dataflows/shioaji_ticks.py` — calls `POST /api/v1/data/ticks` on the Shioaji sidecar (port 21322), fetches all ticks for a given trading day, and aggregates into 12 microstructure metrics
- Metrics computed: total tick count, total volume, avg trade size, VWAP, last price vs VWAP deviation, buy/sell volume split, order flow imbalance index (−1 to +1), block-trade count and % of volume (threshold: ≥10,000 shares/tick), intraday momentum (early vs late session), avg bid-ask spread
- New LangChain tool `tradingagents/agents/utils/tick_tools.py` wrapping the above as `get_tick_microstructure(symbol, date)`
- Exported from `agent_utils.py` alongside existing tools
- `market_analyst.py` updated:
  - Tool added to tool list only for 4–6 digit numeric tickers (Taiwan heuristic)
  - EN and ZH prompts extended with a 5th analysis focus area ("Microstructure" / "籌碼微結構")
  - Kickoff `HumanMessage` instructs the analyst to call the tool with the exact symbol and date
  - If sidecar is offline or returns no data, tool returns a plain-text error string and analyst skips the section — no crash

### 8. Sync TradingAgentsX Watchlist as Named List in Pro Terminal
- **Backend:** `POST /api/shioaji-server/watchlist-sync` in `shioaji_server_routes.py`
  - Fetches all TWSE / TPEx items from the database
  - Formats as `{security_type: "STK", exchange: "TSE"|"OTC", code}` contracts
  - Checks whether a list named `"TradingAgentsX"` already exists via `GET /api/v1/watchlist` on the sidecar; creates or updates accordingly
  - Returns `{synced, list_name, action}`
- **Frontend API:** `api.syncWatchlistToProTerminal()` in `lib/api.ts`
- **UI:** "Sync to Pro Terminal" button added to the Watchlist page toolbar (disabled when no Taiwan tickers exist); two-state loading label; `LineChart` icon spins while syncing

---

## Bugs Fixed

| # | Symptom | Root Cause | Fix |
|---|---------|-----------|-----|
| 1 | "Analysis failed" always shown in UI | `routes.py` used `result.get("message")` but the key was `"error"` | Changed to `result.get("error")` |
| 2 | `sentence-transformers` crash on import | `transformers` 5.13.1 called `is_offline_mode` removed in `huggingface_hub` 0.33.0 | Added `sentence-transformers` as explicit dep via `uv add`; lock resolves to `huggingface-hub 1.16.1` which re-exports the symbol |
| 3 | Progress timeline shows all 14 steps regardless of analyst selection | `AnalysisProgress` had no knowledge of selected analysts | Added `analysts` prop + `activePipeline` filter |
| 4 | TypeScript error: `"cancelled"` not in status type | `TaskStatusResponse.status` union was incomplete | Added `"cancelling" \| "cancelled"` to `types.ts` |
| 5 | `OperationError` crash when opening Trading page | Browser fingerprint-derived crypto key broke on any environment change | Replaced fingerprint with fixed `APP_KEY_MATERIAL` constant |
| 6 | Analysis History shows 0 counts for all tabs | `loadCounts` filtered reports by current locale | Removed language filter entirely |
| 7 | BroadcastChannel cross-origin failure | `:3000` and `:5173` are different origins; `BroadcastChannel` is same-origin only | Migrated to `window.postMessage` with explicit target origin |
| 8 | `?code=` URL param ignored in Pro Terminal main window | `POPOUT_CODE` was only consumed by `<PopoutView>`; main window always defaulted to `items[0]` | Added `initialCodeApplied` ref + one-shot `useEffect` |
| 9 | Stale `proTerminalWindow` module variable reset by HMR | Next.js HMR resets module-level state | Replaced with `window.open('', name)` probe + cross-origin detection |

---

## Architecture Notes

### Cross-Origin Window Communication (`:3000` ↔ `:5173`)
`BroadcastChannel` is strictly same-origin. The solution:
- Watchlist page uses `window.postMessage({ type: 'sj-select-code', code }, targetOrigin)`
- Pro Terminal listens with `window.addEventListener('message', handler)`
- Window identity is tracked by name (`'shioaji-pro-terminal'`) via `window.open('', name)`; cross-origin detection via `.document` access throwing `SecurityError`

### Shioaji Sidecar Watchlist API
- `GET /api/v1/watchlist` — list all named watchlists
- `POST /api/v1/watchlist` — create `{ name, contracts[] }`
- `PUT /api/v1/watchlist/{id}` — replace contracts in existing list
- `DELETE /api/v1/watchlist/{id}` — delete list (two-click confirmation in UI)
- Contract format: `{ security_type: "STK", exchange: "TSE"|"OTC", code: "XXXX" }`

### Pro Terminal Watchlist Delete UX
The trash icon uses a **two-click confirmation** (by design, to prevent accidental deletion):
1. First click → button turns red, label changes to `確認?`, resets after 2.5 s
2. Second click within 2.5 s → calls `DELETE /api/v1/watchlist/{id}`

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/lib/i18n/en.ts` | Added `cancelAnalysis` key |
| `frontend/lib/i18n/zh-TW.ts` | Added `cancelAnalysis` key |
| `frontend/lib/types.ts` | Extended `TaskStatusResponse.status` union |
| `frontend/lib/api.ts` | Added `checkLlmStatus()`, `syncWatchlistToProTerminal()` |
| `frontend/lib/crypto.ts` | Replaced browser fingerprint with fixed `APP_KEY_MATERIAL`; `decrypt()` returns `""` on failure |
| `frontend/components/analysis/LlmStatusIndicator.tsx` | New component — Ollama/LLM server status dot |
| `frontend/components/analysis/AnalysisForm.tsx` | Added `LlmStatusIndicator` above LLM settings section |
| `frontend/components/analysis/AnalysisProgress.tsx` | Added `analysts` prop + `activePipeline` filtering; fixed phase header index |
| `frontend/app/analysis/page.tsx` | Added `selectedAnalysts` state; passes it to `AnalysisProgress` |
| `frontend/app/history/page.tsx` | Removed locale filter from `loadReports` / `loadCounts` |
| `frontend/app/trading/page.tsx` | Persist all Shioaji credentials + simulation flag to localStorage |
| `frontend/app/watchlist/page.tsx` | Added `openInProTerminal()`, Pro Terminal button per Taiwan row, "Sync to Pro Terminal" toolbar button |
| `backend/app/api/routes.py` | Added `GET /api/llm/status` |
| `backend/app/api/shioaji_server_routes.py` | Added `POST /api/shioaji-server/watchlist-sync` |
| `shioaji-pro-app/src/App.tsx` | postMessage listener; `?code=` fix for main window *(git-ignored, local only)* |
| `tradingagents/dataflows/shioaji_ticks.py` | New — fetch + aggregate intraday ticks from Shioaji sidecar |
| `tradingagents/agents/utils/tick_tools.py` | New — `get_tick_microstructure` LangChain tool wrapper |
| `scripts/export_reports_to_md.py` | Added `orderflow_report` section (🌊 委託流向分析) to markdown export |
| `pyproject.toml` | Added `sentence-transformers>=5.6.0` as explicit dependency |
| `uv.lock` | Upgraded `huggingface-hub` 0.33.0 → 1.16.1, `regex`, `tokenizers`, `typer` |
| `test_orderflow.py` | Ad-hoc smoke-test script for orderflow analyst (not committed; run with `uv run python test_orderflow.py`) |
| `tradingagents/agents/utils/agent_utils.py` | Export `get_tick_microstructure` |
| `tradingagents/agents/analysts/market_analyst.py` | Remove tick tool (moved to orderflow analyst); clean up EN/ZH prompts |
| `tradingagents/agents/analysts/orderflow_analyst.py` | New — 5th parallel analyst: order flow + microstructure |
| `tradingagents/agents/utils/agent_states.py` | Added `orderflow_report` field to `AgentState` |
| `tradingagents/graph/conditional_logic.py` | Added `should_continue_orderflow` |
| `tradingagents/graph/setup.py` | Wired orderflow analyst block |
| `tradingagents/graph/trading_graph.py` | Added orderflow tool node, progress node, log state field |
| `tradingagents/dataflows/shioaji_ticks.py` | Added `fetch_raw_ticks()` for PDF renderer (raw sidecar JSON) |
| `backend/app/services/trading_service.py` | Fetch raw tick data post-analysis for Taiwan stocks; store as `tick_data` in result |
| `backend/app/services/pdf_generator.py` | New `_generate_tick_chart()` matplotlib chart; new `_build_tick_page()`; i18n labels EN/ZH-TW |
| `backend/app/services/download_service.py` | Thread `tick_data` through `create_combined_pdf()` signature |
| `backend/app/api/routes.py` | Thread `tick_data` through `/pdf/download` and `/pdf/generate` endpoints |

---

## Commits (this period)

```
a18bb3d  Update bring-up report with dependency fix details
7f2d904  Add sentence-transformers as explicit dependency; upgrade huggingface-hub
2006f4b  Add orderflow_report section to markdown export
6df59d1  Add orderflow analyst as 5th parallel analyst in propagation phase
9c20d40  Add intraday tick microstructure page to analysis PDF
a658cf7  Update bring-up report with tick microstructure feature and full commit log
965e64d  Add bring-up report
f430a3b  Add intraday tick microstructure to market analyst (Taiwan stocks)
0b8a076  Sync TradingAgentsX watchlist as named list in Shioaji Pro Terminal
f3fd9c4  Fix Pro Terminal ticker switch — handle ?code= on mount and improve window detection
3089ebf  Fix Pro Terminal ticker switch using postMessage instead of BroadcastChannel
252a9ce  Add Pro Terminal button to watchlist for Taiwan stocks
c687063  Persist all Trading page credentials across sessions
662c622  Fix OperationError on Pro Terminal open due to unstable key derivation
3125a8e  Fix history page showing 0 counts due to language filter
d4824ab  Add LLM server status indicator to analysis form
66a54b7  Add markdown analysis reports and export script
171691c  Switch default LLM to qwen2.5:14b-16k and fix Ollama GPU detection
3e9ab2b  Default analysis form to custom/qwen2.5:14b-32k (Ollama local model)
c77d5e1  Fix Ollama models triggering API key alert in AnalysisForm
c57a027  Switch default LLM to qwen2.5:14b-32k (32768 token context)
```

---

## Known Limitations / Follow-up

- `shioaji-pro-app/` is listed in `.gitignore` — App.tsx changes (postMessage listener, `?code=` fix) live only in the local working tree and must be manually re-applied after any clean checkout
- The "Sync to Pro Terminal" button requires the Shioaji sidecar to be running; it will show a toast error if the sidecar is offline
- Watchlist delete in Pro Terminal requires **two clicks** within 2.5 s — this is intentional but worth noting for new users
- Tick microstructure only available for Taiwan stocks (TWSE/TPEx) via Shioaji sidecar; no equivalent tick source for US stocks currently
- Tick data volumes in Shioaji are in shares (not 張/lots); block-trade threshold is set to ≥10,000 shares (10 張) per tick — adjust `LARGE_LOT_THRESHOLD` in `shioaji_ticks.py` if needed
- Tick PDF page only appears when the Shioaji sidecar is running and logged in at the time the PDF is generated (post-analysis fetch); if sidecar goes offline after analysis but before PDF download, the page will be missing — no error shown
- Orderflow analyst runs after the other analysts in the sequential propagation chain; for US stocks it only calls `get_stock_data` (no tick source), so the microstructure deep-dive section will contain volume-proxy analysis only
