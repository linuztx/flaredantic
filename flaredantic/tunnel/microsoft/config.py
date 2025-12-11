from dataclasses import dataclass
from ...base.config import BaseConfig


@dataclass
class MicrosoftConfig(BaseConfig):
    """Configuration for Microsoft Dev Tunnel"""
    tunnel_id: str = "flaredantic"
    device_login: bool = True
