from dataclasses import dataclass
from ...base.config import BaseConfig
from pathlib import Path

@dataclass
class ServeoConfig(BaseConfig):
    """Configuration for Serveo tunnel"""
    ssh_dir: str = Path.home() / ".flaredantic" / "ssh"
    known_host_file: str = ssh_dir / "known_hosts"
    tcp: bool = False