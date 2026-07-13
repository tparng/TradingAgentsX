"""
Manages the shioaji HTTP sidecar server process (port 21322).
The sidecar is the binary bundled with shioaji-pro-app; it exposes a REST+SSE
API that shioaji-pro-app's frontend talks to directly.
"""
import logging
import os
import re
import subprocess
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

SIDECAR_PORT = 21322
SIDECAR_BIN = (
    Path(__file__).parents[3]
    / "shioaji-pro-app/src-tauri/binaries/shioaji-x86_64-unknown-linux-gnu"
)


class ShioajiServerManager:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, api_key: str, secret_key: str, simulation: bool = True) -> dict:
        with self._lock:
            if self._process and self._process.poll() is None:
                return {"status": "already_running", "port": SIDECAR_PORT}

            if not SIDECAR_BIN.exists():
                raise RuntimeError(f"Sidecar binary not found: {SIDECAR_BIN}")

            env = os.environ.copy()
            env["SJ_API_KEY"]   = api_key
            env["SJ_SEC_KEY"]   = secret_key
            env["SJ_HTTP_ADDR"] = f"127.0.0.1:{SIDECAR_PORT}"
            if not simulation:
                env["SJ_PRODUCTION"] = "true"
            else:
                env.pop("SJ_PRODUCTION", None)

            cmd = [str(SIDECAR_BIN), "server", "start", "--no-open"]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            logger.info(f"[shioaji-server] started PID {self._process.pid} simulation={simulation}")

        # Wait up to 60 s — real-credential login loads ~50k contracts and takes 20–40 s
        for _ in range(120):
            time.sleep(0.5)
            if self._is_healthy():
                return {"status": "started", "port": SIDECAR_PORT, "simulation": simulation}
            if self._process.poll() is not None:
                out = self._process.stdout.read().decode(errors="replace") if self._process.stdout else ""
                out = re.sub(r'\x1b\[[0-9;]*m', '', out)  # strip ANSI colour codes
                raise RuntimeError(f"Sidecar exited early: {out[:2000]}")

        raise RuntimeError("Sidecar did not become healthy within 60 s")

    def stop(self) -> dict:
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                logger.info("[shioaji-server] stopped")
                self._process = None
                return {"status": "stopped"}
            return {"status": "not_running"}

    def status(self) -> dict:
        with self._lock:
            running = self._process is not None and self._process.poll() is None
        healthy = self._is_healthy() if running else False
        return {
            "running": running,
            "healthy": healthy,
            "port": SIDECAR_PORT,
            "pid": self._process.pid if running else None,
        }

    # ── internal ─────────────────────────────────────────────────────────────

    def _is_healthy(self) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(
                f"http://127.0.0.1:{SIDECAR_PORT}/api/v1/health", timeout=2
            ) as r:
                return r.status == 200
        except Exception:
            return False


shioaji_server_manager = ShioajiServerManager()
