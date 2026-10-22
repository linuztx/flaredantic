from dataclasses import dataclass, field
from typing import Optional
from ...base.config import BaseConfig


@dataclass
class TailscaleConfig(BaseConfig):
    """Configuration for Tailscale Funnel"""
    hostname: str = "flaredantic"
    auth_key: Optional[str] = field(default=None, repr=False)
    use_system: bool = False
