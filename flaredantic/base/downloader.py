from abc import ABC, abstractmethod
from pathlib import Path
import logging

class BaseDownloader(ABC):
    """Base class for binary downloaders"""

    def __init__(self, bin_dir: Path, verbose: bool = False) -> None:
        self.bin_dir = bin_dir
        self.logger = logging.Logger
        self.verbose = verbose

    @abstractmethod
    def download(self) -> Path:
        """
        Download and install the binary

        Returns:
            Path to installed binary
        """
        pass
