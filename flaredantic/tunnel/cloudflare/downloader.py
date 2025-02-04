import platform
import requests
import tarfile
from pathlib import Path
from typing import Tuple
from tqdm import tqdm
from ...base.downloader import BaseDownloader
from ...exceptions import CloudflaredError, DownloadError
from ...logging_config import setup_logger

class FlareDownloader(BaseDownloader):
    def __init__(self, bin_dir: Path, verbose: bool = False):
        super().__init__(bin_dir, verbose)
        self.logger = setup_logger(verbose)

    @property
    def _platform_info(self) -> Tuple[str, str]:
        """Get current platform information"""
        system = platform.system().lower()
        arch = platform.machine().lower()
        return system, arch

    def _get_download_url(self) -> Tuple[str, str]:
        """Get appropriate download URL for current platform"""
        system, arch = self._platform_info
        base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
        
        if system == "darwin":
            filename = f"cloudflared-darwin-{'arm64' if arch == 'arm64' else 'amd64'}.tgz"
        elif system == "linux":
            arch_map = {
                "x86_64": "amd64",
                "amd64": "amd64",
                "arm64": "arm64",
                "aarch64": "arm64",
                "arm": "arm",
            }
            filename = f"cloudflared-linux-{arch_map.get(arch, '386')}"
        elif system == "windows":
            filename = "cloudflared-windows-amd64.exe"
        else:
            raise CloudflaredError(f"Unsupported platform: {system} {arch}")
            
        return base_url + filename, filename

    def download(self) -> Path:
        """
        Download and install cloudflared binary
        
        Returns:
            Path to installed cloudflared binary
        """
        system, _ = self._platform_info
        executable_name = "cloudflared.exe" if system == "windows" else "cloudflared"
        install_path = self.bin_dir / executable_name

        # Return if already exists
        if install_path.exists():
            self.logger.debug(f"Using existing cloudflared binary at: {install_path}")
            return install_path

        download_url, filename = self._get_download_url()
        download_path = self.bin_dir / filename

        try:
            self.logger.info(f"Downloading cloudflared from: {download_url}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # Download with progress bar (always show progress)
            total_size = int(response.headers.get('content-length', 0))
            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc="Downloading cloudflared",
                disable=False  # Never disable progress bar
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            if filename.endswith('.tgz'):
                self.logger.debug("Extracting .tgz archive...")
                with tarfile.open(download_path, "r:gz") as tar:
                    tar.extract("cloudflared", str(self.bin_dir))
                download_path.unlink()
            else:
                self.logger.debug(f"Moving binary to: {install_path}")
                download_path.rename(install_path)

            # Set executable permissions
            if system != "windows":
                self.logger.debug("Setting executable permissions")
                install_path.chmod(0o755)

            self.logger.info("Successfully installed cloudflared binary")
            return install_path

        except Exception as e:
            self.logger.error(f"Failed to download cloudflared: {str(e)}")
            raise DownloadError(f"Failed to download cloudflared: {str(e)}") from e 