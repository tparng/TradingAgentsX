"""
Manages the shioaji HTTP sidecar server process (port 21322).
The sidecar is the binary bundled with shioaji-pro-app; it exposes a REST+SSE
API that shioaji-pro-app's frontend talks to directly.
"""
import collections
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
        self._log_lines: collections.deque = collections.deque(maxlen=50)
        self._reader: threading.Thread | None = None

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, api_key: str, secret_key: str, simulation: bool = True,
              ca_path: str = "", ca_passwd: str = "") -> dict:
        with self._lock:
            if self._process and self._process.poll() is None:
                return {"status": "already_running", "port": SIDECAR_PORT}

            # Another process may already own the port (e.g. from a prior manual run).
            # If it's healthy, adopt it; if not, kill it so we can bind the port.
            if self._is_healthy():
                return {"status": "already_running", "port": SIDECAR_PORT}
            self._kill_port()

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
            if ca_path:
                env["SJ_CA_PATH"]   = ca_path
            if ca_passwd:
                env["SJ_CA_PASSWD"] = ca_passwd

            cmd = [str(SIDECAR_BIN), "server", "start", "--no-open"]

            self._log_lines.clear()
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            # Background reader captures output continuously — not just at startup
            self._reader = threading.Thread(
                target=self._read_output,
                args=(self._process,),
                daemon=True,
            )
            self._reader.start()
            logger.info(f"[shioaji-server] started PID {self._process.pid} simulation={simulation}")

        # Wait up to 60 s — real-credential login loads ~50k contracts and takes 20–40 s
        for _ in range(120):
            time.sleep(0.5)
            if self._is_healthy():
                log_text = "\n".join(self._log_lines)
                result: dict = {"status": "started", "port": SIDECAR_PORT, "simulation": simulation}
                ca_fail = re.search(r'Failed to activate CA[^\n]*', log_text, re.IGNORECASE)
                if ca_fail:
                    result["ca_warning"] = ca_fail.group(0)
                return result
            if self._process.poll() is not None:
                # Give reader thread a moment to flush remaining lines
                if self._reader:
                    self._reader.join(timeout=2)
                out = "\n".join(self._log_lines)
                raise RuntimeError(f"Sidecar exited early:\n{out[:2000]}")

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
            managed = self._process is not None and self._process.poll() is None
            pid = self._process.pid if managed else None
        healthy = self._is_healthy()
        return {
            "running": managed or healthy,
            "healthy": healthy,
            "port": SIDECAR_PORT,
            "pid": pid,
            "last_output": list(self._log_lines)[-20:],
        }

    # ── internal ─────────────────────────────────────────────────────────────

    def _read_output(self, proc: subprocess.Popen) -> None:
        """Read process stdout in background, keeping last 50 lines for diagnostics."""
        try:
            for raw in proc.stdout:
                line = raw.decode(errors="replace").rstrip()
                line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                self._log_lines.append(line)
                logger.debug(f"[shioaji-server] {line}")
        except Exception:
            pass

    def _kill_port(self) -> None:
        """Kill any process currently bound to SIDECAR_PORT so we can rebind."""
        try:
            result = subprocess.run(
                ["fuser", f"{SIDECAR_PORT}/tcp"],
                capture_output=True, text=True,
            )
            for pid_str in result.stdout.split():
                try:
                    import signal
                    os.kill(int(pid_str), signal.SIGTERM)
                    logger.info(f"[shioaji-server] killed stale PID {pid_str} on port {SIDECAR_PORT}")
                except (ValueError, ProcessLookupError):
                    pass
            if result.stdout.strip():
                time.sleep(1)  # give the OS a moment to release the port
        except FileNotFoundError:
            pass  # fuser not available on this system

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
