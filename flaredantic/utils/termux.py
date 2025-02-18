import os
import shutil
from pathlib import Path

def is_termux() -> bool:
    """Check if running in Termux"""
    return "TERMUX_VERSION" in os.environ

def install_cloudflared() -> Path:
    """
    Install termux official cloudflared package if not already installed
    """
    if shutil.which("cloudflared") is None:
        os.system("pkg install cloudflared -y")
    return Path(shutil.which("cloudflared"))