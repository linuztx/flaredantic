import platform
import requests
from pathlib import Path
from typing import Tuple
from tqdm import tqdm
from ...base.downloader import BaseDownloader
from ...core.exceptions import DownloadError
from ...core.logging_config import setup_logger


class MicrosoftDownloader(BaseDownloader):
    """
    Downloader for Microsoft DevTunnel binary
    """
    def __init__(self, bin_dir: Path, verbose: bool = False):
        """
        Initialize downloader

        Args:
            bin_dir: Directory to install binary
            verbose: Enable verbose logging
        """
        super().__init__(bin_dir, verbose)
        self.logger = setup_logger(verbose)

    @property
    def _platform_info(self) -> Tuple[str, str]:
        """
        Get current platform information

        Returns:
            Tuple of (system, architecture)
        """
        system = platform.system().lower()
        arch = platform.machine().lower()
        return system, arch

    def _get_download_url(self) -> Tuple[str, str]:
        """
        Get download URL for current platform

        Returns:
            Tuple of (download_url, binary_name)

        Raises:
            DownloadError: If platform is not supported
        """
        system, arch = self._platform_info
        base = "https://tunnelsassetsprod.blob.core.windows.net/cli/"

        if system == "darwin":
            filename = "osx-arm64-devtunnel" if arch == "arm64" else "osx-x64-devtunnel"
        elif system == "linux":
            if arch in ("arm64", "aarch64"):
                filename = "linux-arm64-devtunnel"
            else:
                filename = "linux-x64-devtunnel"
        else:
            raise DownloadError(f"Unsupported platform: {system} {arch}")

        return base + filename, "microsoft"

    def download(self) -> Path:
        """
        Download and install Microsoft DevTunnel binary

        Returns:
            Path to installed binary

        Raises:
            DownloadError: If download fails
        """
        install_path = self.bin_dir / "microsoft"

        if install_path.exists():
            return install_path

        url, _ = self._get_download_url()
        download_path = self.bin_dir / "microsoft.download"

        try:
            self.logger.info(f"Downloading Microsoft DevTunnel from: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc="Downloading Microsoft DevTunnel",
                disable=False
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            download_path.rename(install_path)
            install_path.chmod(0o755)
            self.logger.info("Successfully installed Microsoft DevTunnel binary")
            return install_path
        except Exception as e:
            self.logger.error(f"Failed to download Microsoft DevTunnel: {str(e)}")
            raise DownloadError(f"Failed to download Microsoft DevTunnel: {str(e)}") from e
