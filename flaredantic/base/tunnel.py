from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import logging

class BaseTunnel(ABC):
    """Base class for all tunnel implementations"""

    def __init__(self) -> None:
        self.tunnel_url: Optional[str] = None
        self.logger: Optional[logging.Logger] = None
        self.binary_path: Optional[Path] = None

    @abstractmethod
    def start(self) -> str:
        """Start the tunnel and return the URL"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the tunnel"""
        pass

    def __enter__(self):
        """Context manager support: starts the tunnel."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure tunnel is stopped when exiting context."""
        self.stop()

    async def __aenter__(self):
        """Asynchronous context manager support: starts the tunnel."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure tunnel is stopped when exiting async context."""
        return self.__exit__(exc_type, exc_val, exc_tb)