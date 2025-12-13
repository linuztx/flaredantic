from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
import logging
from ..core.notify import notifier, NotifyEvent


class BaseDownloader(ABC):
    """Base class for binary downloaders"""

    def __init__(self, bin_dir: Path, verbose: bool = False) -> None:
        self.bin_dir = bin_dir
        self.logger = logging.Logger
        self.verbose = verbose

    def notify(self, event: NotifyEvent, message: str, data: Optional[Any] = None) -> None:
        """Send notification to subscribers"""
        notifier.notify(event, message, data)

    @abstractmethod
    def download(self) -> Path:
        """
        Download and install the binary

        Returns:
            Path to installed binary
        """
        pass
