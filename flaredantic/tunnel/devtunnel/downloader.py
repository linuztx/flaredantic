import platform
import requests
from pathlib import Path
from typing import Tuple
from tqdm import tqdm
from ...base.downloader import BaseDownloader
from ...core.exceptions import DownloadError
from ...core.logging_config import setup_logger


class DevTunnelDownloader(BaseDownloader):
    def __init__(self, bin_dir: Path, verbose: bool = False):
        super().__init__(bin_dir, verbose)
        self.logger = setup_logger(verbose)

    @property
    def _platform_info(self) -> Tuple[str, str]:
        system = platform.system().lower()
        arch = platform.machine().lower()
        return system, arch

    def _get_download_url(self) -> Tuple[str, str]:
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

        return base + filename, "devtunnel"

    def download(self) -> Path:
        install_path = self.bin_dir / "devtunnel"

        if install_path.exists():
            return install_path

        url, _ = self._get_download_url()
        download_path = self.bin_dir / "devtunnel.download"

        try:
            self.logger.info(f"Downloading devtunnel from: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc="Downloading devtunnel",
                disable=False
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            download_path.rename(install_path)
            install_path.chmod(0o755)
            self.logger.info("Successfully installed devtunnel binary")
            return install_path
        except Exception as e:
            self.logger.error(f"Failed to download devtunnel: {str(e)}")
            raise DownloadError(f"Failed to download devtunnel: {str(e)}") from e

