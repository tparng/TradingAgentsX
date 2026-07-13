#!/usr/bin/env bash
# TradingAgentsX launcher — starts backend, frontend, then opens browser.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=3000
BROWSER="google-chrome"

# ── helpers ──────────────────────────────────────────────────────────────────

log() { echo "[TradingAgentsX] $*"; }

wait_for_port() {
  local port=$1 label=$2 tries=0
  log "Waiting for $label on port $port..."
  until curl -sf "http://localhost:$port" -o /dev/null 2>/dev/null; do
    sleep 1
    tries=$((tries + 1))
    if [ $tries -ge 60 ]; then
      log "ERROR: $label did not start within 60 s"
      exit 1
    fi
  done
  log "$label is ready."
}

# ── backend ───────────────────────────────────────────────────────────────────

if curl -sf "http://localhost:$BACKEND_PORT/api/health" -o /dev/null 2>/dev/null; then
  log "Backend already running on port $BACKEND_PORT."
else
  log "Starting backend..."
  cd "$REPO"
  source .venv/bin/activate
  python -m backend > /tmp/tradingagentsx-backend.log 2>&1 &
  BACKEND_PID=$!
  log "Backend PID: $BACKEND_PID"
  wait_for_port $BACKEND_PORT "Backend"
fi

# ── frontend ──────────────────────────────────────────────────────────────────

if curl -sf "http://localhost:$FRONTEND_PORT" -o /dev/null 2>/dev/null; then
  log "Frontend already running on port $FRONTEND_PORT."
else
  log "Starting frontend..."
  cd "$REPO/frontend"
  if [ ! -d node_modules ]; then
    log "Installing frontend dependencies (first run)..."
    npm install
  fi
  npm run dev > /tmp/tradingagentsx-frontend.log 2>&1 &
  FRONTEND_PID=$!
  log "Frontend PID: $FRONTEND_PID"
  wait_for_port $FRONTEND_PORT "Frontend"
fi

# ── open browser ──────────────────────────────────────────────────────────────

log "Opening browser..."
$BROWSER "http://localhost:$FRONTEND_PORT" &

log "TradingAgentsX is running."
log "  Frontend: http://localhost:$FRONTEND_PORT"
log "  Backend:  http://localhost:$BACKEND_PORT/docs"
log "  Logs:     /tmp/tradingagentsx-backend.log  /tmp/tradingagentsx-frontend.log"
