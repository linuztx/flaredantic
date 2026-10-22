import platform
import requests
import shutil
import tarfile
import time
from pathlib import Path
from typing import Tuple
from tqdm import tqdm
from ...base.downloader import BaseDownloader
from ...core.exceptions import TailscaleDownloadError
from ...core.logging_config import setup_logger
from ...core.notify import NotifyEvent


class TailscaleDownloader(BaseDownloader):
    """
    Downloader for the Tailscale static binaries (tailscale and tailscaled)
    """
    PACKAGES_URL = "https://pkgs.tailscale.com/stable/"

    def __init__(self, bin_dir: Path, verbose: bool = False):
        """
        Initialize downloader

        Args:
            bin_dir: Directory to install binaries
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
        Get download URL of the latest stable release for current platform

        Returns:
            Tuple of (download_url, archive_name)

        Raises:
            TailscaleDownloadError: If platform is not supported
        """
        system, arch = self._platform_info
        arch_map = {
            "x86_64": "amd64",
            "amd64": "amd64",
            "aarch64": "arm64",
            "arm64": "arm64",
            "armv6l": "arm",
            "armv7l": "arm",
            "armv8l": "arm",
            "i386": "386",
            "i686": "386",
            "riscv64": "riscv64",
        }
        # Tailscale only publishes static binaries for Linux
        if system != "linux" or arch not in arch_map:
            raise TailscaleDownloadError(f"Unsupported platform: {system} {arch}")

        response = requests.get(self.PACKAGES_URL, params={"mode": "json"}, timeout=30)
        response.raise_for_status()
        filename = response.json()["Tarballs"][arch_map[arch]]
        return self.PACKAGES_URL + filename, filename

    def download(self) -> Path:
        """
        Download and install the Tailscale binaries

        Returns:
            Path to installed tailscale CLI (tailscaled is installed next to it)

        Raises:
            TailscaleDownloadError: If download fails
        """
        cli_path = self.bin_dir / "tailscale"
        daemon_path = self.bin_dir / "tailscaled"

        if cli_path.exists() and daemon_path.exists():
            self.logger.debug(f"Using existing Tailscale binaries in: {self.bin_dir}")
            return cli_path

        try:
            download_url, filename = self._get_download_url()
            download_path = self.bin_dir / filename

            self.logger.info(f"Downloading Tailscale from: {download_url}")
            self.notify(NotifyEvent.DOWNLOADING, "Downloading Tailscale binaries...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_reported_time = 0.0

            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc="Downloading Tailscale",
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

            self.logger.debug("Extracting Tailscale binaries...")
            with tarfile.open(download_path, "r:gz") as tar:
                for member in tar.getmembers():
                    name = Path(member.name).name
                    if not member.isfile() or name not in ("tailscale", "tailscaled"):
                        continue
                    # Extract under a temporary name so an interrupted install is never reused
                    partial_path = self.bin_dir / f"{name}.part"
                    with tar.extractfile(member) as src, open(partial_path, 'wb') as dst:  # type: ignore[union-attr]
                        shutil.copyfileobj(src, dst)
                    partial_path.chmod(0o755)
                    partial_path.replace(self.bin_dir / name)
            download_path.unlink()

            if not (cli_path.exists() and daemon_path.exists()):
                raise TailscaleDownloadError(f"tailscale binaries not found in {filename}")

            self.logger.info("Successfully installed Tailscale binaries")
            self.notify(NotifyEvent.DOWNLOAD_COMPLETE, "Tailscale binaries installed successfully")
            return cli_path
        except Exception as e:
            self.logger.error(f"Failed to download Tailscale: {str(e)}")
            self.notify(NotifyEvent.ERROR, f"Failed to download Tailscale: {str(e)}")
            raise TailscaleDownloadError(f"Failed to download Tailscale: {str(e)}") from e
