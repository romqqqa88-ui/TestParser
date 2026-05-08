from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


WORKSPACE = Path(r"C:\workspace")
RUN_ONCE = WORKSPACE / "scripts" / "run_once_parse.py"
PID_FILE = WORKSPACE / "exports" / "loop.pid"
SLEEP_SECONDS = 120


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:55433/avito_parser"
    env["ALEMBIC_DATABASE_URL"] = "postgresql://postgres@127.0.0.1:55433/avito_parser"
    env["REQUEST_COOKIE_FILE"] = str(WORKSPACE / "storage" / "avito_cookies.txt")
    env["NEW_LISTINGS_FILE"] = "new_listings.jsonl"
    return env


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _handle_exit(*_: object) -> None:
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    raise SystemExit(0)


def main() -> int:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    if PID_FILE.exists():
        try:
            existing_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if _is_running(existing_pid):
                print(f"Loop is already running (PID {existing_pid}).")
                return 0
        except (ValueError, OSError):
            pass
        PID_FILE.unlink(missing_ok=True)

    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)

    env = _build_env()
    try:
        while True:
            completed = subprocess.run([sys.executable, str(RUN_ONCE)], cwd=str(WORKSPACE), env=env, check=False)
            if completed.returncode != 0:
                print(f"run_once_parse.py failed with code {completed.returncode}; retrying in {SLEEP_SECONDS}s.")
            time.sleep(SLEEP_SECONDS)
    finally:
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
