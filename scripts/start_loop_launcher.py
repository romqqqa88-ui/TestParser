from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    workspace = Path(r"C:\workspace")
    script = workspace / "scripts" / "start_loop.ps1"
    if not script.exists():
        print(f"Missing script: {script}")
        return 1
    completed = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=str(workspace),
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
