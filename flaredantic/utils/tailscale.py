import os
import platform
import shutil
from pathlib import Path
from typing import Optional


def find_tailscale() -> Optional[Path]:
    """Find the Tailscale CLI installed on this machine"""
    path = shutil.which("tailscale")
    if path:
        return Path(path)

    # The macOS and Windows apps don't always put the CLI on PATH
    system = platform.system().lower()
    if system == "darwin":
        app_cli = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
    elif system == "windows":
        app_cli = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale" / "tailscale.exe"
    else:
        return None
    return app_cli if app_cli.exists() else None
