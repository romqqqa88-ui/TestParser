from __future__ import annotations

import subprocess
from pathlib import Path


PID_FILE = Path(r"C:\workspace\exports\loop.pid")


def main() -> int:
    if not PID_FILE.exists():
        print("Loop process not found.")
        return 0

    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)
        print("Loop process not found.")
        return 0

    completed = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True, check=False)
    if completed.returncode == 0:
        print(f"Stopped PID {pid}")
        PID_FILE.unlink(missing_ok=True)
        return 0

    print(completed.stdout.strip() or completed.stderr.strip() or "Failed to stop process.")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
