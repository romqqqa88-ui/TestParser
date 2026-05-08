from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    workspace = Path(r"C:\workspace")
    script = workspace / "scripts" / "stop_loop.ps1"
    if not script.exists():
        print(f"Missing script: {script}")
        return 1
    completed = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or completed.stderr or "").strip()
    if output:
        print(output)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
