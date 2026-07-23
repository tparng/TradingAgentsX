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
| 2 | `sentence-transformers` crash on import | `transformers` 5.13.1 called `is_offline_mode` removed in `huggingface_hub` 0.33.0 | Pinned `transformers>=5.14.0` |
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

---

## Commits (this period)

```
0b8a076  Sync TradingAgentsX watchlist as named list in Shioaji Pro Terminal
f3fd9c4  Add watchlist–Pro Terminal integration and button for Taiwan stocks
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
