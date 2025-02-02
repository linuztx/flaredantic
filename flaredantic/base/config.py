from abc import ABC
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BaseConfig(ABC):
    """Base configuration for all tunnel implementations"""
    port: int
    bin_dir: Path = Path.home() / ".flaredantic"
    timeout: int = 30
    verbose: bool = False