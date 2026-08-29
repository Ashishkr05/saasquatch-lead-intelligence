"""Start the FastAPI and Vite development servers together.

Run after installing backend and frontend dependencies:
    python scripts/dev.py
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def python_executable() -> str:
    windows_venv = ROOT / ".venv" / "Scripts" / "python.exe"
    unix_venv = ROOT / ".venv" / "bin" / "python"
    if windows_venv.exists():
        return str(windows_venv)
    if unix_venv.exists():
        return str(unix_venv)
    return sys.executable


def npm_executable() -> str:
    command = "npm.cmd" if os.name == "nt" else "npm"
    resolved = shutil.which(command)
    if not resolved:
        raise SystemExit("npm was not found. Install Node.js 20+ and run npm install in frontend/.")
    return resolved


def main() -> None:
    backend = subprocess.Popen(
        [python_executable(), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=BACKEND,
    )
    frontend = subprocess.Popen(
        [npm_executable(), "run", "dev", "--", "--host", "127.0.0.1"],
        cwd=FRONTEND,
    )
    processes = [backend, frontend]
    print("\nScout is starting:")
    print("  App:      http://127.0.0.1:5173")
    print("  API docs: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop both services.\n")

    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    failed = [process.returncode for process in processes if process.returncode not in (None, 0, -15)]
    if failed:
        raise SystemExit(f"A development service exited unexpectedly: {failed}")


if __name__ == "__main__":
    main()

