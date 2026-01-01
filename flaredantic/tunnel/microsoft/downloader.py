import platform
import requests
import time
from pathlib import Path
from typing import Tuple
from tqdm import tqdm
from ...base.downloader import BaseDownloader
from ...core.exceptions import MicrosoftDownloadError
from ...core.logging_config import setup_logger
from ...core.notify import NotifyEvent


class MicrosoftDownloader(BaseDownloader):
    """
    Downloader for Microsoft Dev Tunnels binary
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
            MicrosoftDownloadError: If platform is not supported
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
        elif system == "windows":
            filename = "devtunnel.exe"
        else:
            raise MicrosoftDownloadError(f"Unsupported platform: {system} {arch}")

        return base + filename, filename

    def download(self) -> Path:
        """
        Download and install Microsoft Dev Tunnels binary

        Returns:
            Path to installed binary

        Raises:
            MicrosoftDownloadError: If download fails
        """
        system, _ = self._platform_info
        executable_name = "devtunnel.exe" if system == "windows" else "devtunnel"
        install_path = self.bin_dir / executable_name

        if install_path.exists():
            self.logger.debug(f"Using existing Microsoft Dev Tunnels binary at: {install_path}")
            return install_path

        download_url, filename = self._get_download_url()
        download_path = self.bin_dir / filename

        try:
            self.logger.info(f"Downloading Microsoft Dev Tunnels from: {download_url}")
            self.notify(NotifyEvent.DOWNLOADING, "Downloading Microsoft Dev Tunnels binary...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_reported_time = 0.0

            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc="Downloading Microsoft Dev Tunnels",
                disable=False
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
                    downloaded += size
                    
                    if total_size:
                        current_time = time.time()
                        progress = (downloaded / total_size * 100)
                        # Throttle updates to every 0.1 seconds or when complete
                        if (current_time - last_reported_time >= 0.1) or progress >= 100.0:
                            self.notify(NotifyEvent.DOWNLOAD_PROGRESS, f"Downloading: {progress:.1f}%", {
                                "downloaded": downloaded,
                                "total": total_size,
                                "percent": progress
                            })
                            last_reported_time = current_time

            self.logger.debug(f"Moving binary to: {install_path}")
            download_path.rename(install_path)

            if system != "windows":
                self.logger.debug("Setting executable permissions")
                install_path.chmod(0o755)
                
            self.logger.info("Successfully installed Microsoft Dev Tunnels binary")
            self.notify(NotifyEvent.DOWNLOAD_COMPLETE, "Microsoft Dev Tunnels binary installed successfully")
            return install_path
        except Exception as e:
            self.logger.error(f"Failed to download Microsoft Dev Tunnels: {str(e)}")
            self.notify(NotifyEvent.ERROR, f"Failed to download Microsoft Dev Tunnels: {str(e)}")
            raise MicrosoftDownloadError(f"Failed to download Microsoft Dev Tunnels: {str(e)}") from e
