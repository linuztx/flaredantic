from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from ...base.config import BaseConfig


@dataclass
class TailscaleConfig(BaseConfig):
    """Configuration for Tailscale Funnel"""
    https_port: int = 443  # Public Funnel port: 443, 8443 or 10000
    use_system: bool = True  # Use the Tailscale already running on this machine
    login_timeout: int = 300  # Seconds to wait for browser login or Funnel approval

    # Used by the node flaredantic runs itself when no Tailscale is running (Linux only)
    hostname: str = "flaredantic"
    auth_key: Optional[str] = None
    state_dir: Path = Path.home() / ".flaredantic" / "tailscale-state"
