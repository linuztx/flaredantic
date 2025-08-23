from dataclasses import dataclass
from ...base.config import BaseConfig
from pathlib import Path

@dataclass
class ServeoConfig(BaseConfig):
    """Configuration for Serveo tunnel"""
    ssh_dir: Path = Path.home() / ".flaredantic" / "ssh"
    known_host_file: Path = Path.home() / ".flaredantic" / "ssh" / "known_hosts"
    tcp: bool = False