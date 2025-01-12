import platform
import requests
import subprocess
import threading
import tarfile
import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from tqdm import tqdm
from .exceptions import CloudflaredError, DownloadError, TunnelError

# logging
logging.basicConfig(
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

GREEN = "\033[92m"
RESET = "\033[0m"

@dataclass
class TunnelConfig:
    port: int
    bin_dir: Path = Path.home() / ".flaredantic"
    timeout: int = 30
    quiet: bool = False

class FlareTunnel:
    def __init__(self, config: Union[TunnelConfig, dict]):
        """
        Initialize FlareTunnel with configuration
        
        Args:
            config: TunnelConfig object or dict with configuration parameters
        """
        if isinstance(config, dict):
            self.config = TunnelConfig(**config)
        else:
            self.config = config
            
        self.cloudflared_path: Optional[Path] = None
        self.tunnel_process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self._stop_event = threading.Event()
        
        # Ensure bin directory exists
        self.config.bin_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _platform_info(self) -> tuple[str, str]:
        """Get current platform information"""
        system = platform.system().lower()
        arch = platform.machine().lower()
        return system, arch

    def _get_download_url(self) -> tuple[str, str]:
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

    def download_cloudflared(self) -> Path:
        """
        Download and install cloudflared binary
        
        Returns:
            Path to installed cloudflared binary
        """
        system, _ = self._platform_info
        executable_name = "cloudflared.exe" if system == "windows" else "cloudflared"
        install_path = self.config.bin_dir / executable_name

        # Return if already exists
        if install_path.exists():
            self.cloudflared_path = install_path
            return install_path

        download_url, filename = self._get_download_url()
        download_path = self.config.bin_dir / filename

        try:
            logger.info(f"Downloading cloudflared from: {download_url}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # Download with progress bar
            total_size = int(response.headers.get('content-length', 0))
            with open(download_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                disable=self.config.quiet
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            if filename.endswith('.tgz'):
                with tarfile.open(download_path, "r:gz") as tar:
                    tar.extract("cloudflared", str(self.config.bin_dir))
                download_path.unlink()
            else:
                download_path.rename(install_path)

            # Set executable permissions
            if system != "windows":
                install_path.chmod(0o755)

            self.cloudflared_path = install_path
            return install_path

        except Exception as e:
            raise DownloadError(f"Failed to download cloudflared: {str(e)}") from e

    def _extract_tunnel_url(self, process: subprocess.Popen) -> None:
        """Extract tunnel URL from cloudflared output"""
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break

            line = line if isinstance(line, str) else line.decode('utf-8')
            if "trycloudflare.com" in line and "https://" in line:
                start = line.find("https://")
                end = line.find("trycloudflare.com") + len("trycloudflare.com")
                self.tunnel_url = line[start:end].strip()
                if not self.config.quiet:
                    logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                return

    def start(self) -> str:
        """
        Start the cloudflare tunnel
        
        Returns:
            Tunnel URL once available
        """
        if not self.cloudflared_path:
            self.download_cloudflared()

        logger.info("Starting Cloudflare tunnel...")
        try:
            self.tunnel_process = subprocess.Popen(
                [
                    str(self.cloudflared_path),
                    "tunnel",
                    "--url",
                    f"http://localhost:{self.config.port}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )

            url_thread = threading.Thread(
                target=self._extract_tunnel_url,
                args=(self.tunnel_process,),
                daemon=True
            )
            url_thread.start()
            url_thread.join(timeout=self.config.timeout)

            if not self.tunnel_url:
                raise TunnelError("Timeout waiting for tunnel URL")

            return self.tunnel_url

        except Exception as e:
            self.stop()
            raise TunnelError(f"Failed to start tunnel: {str(e)}") from e

    def stop(self) -> None:
        """Stop the cloudflare tunnel"""
        self._stop_event.set()
        if self.tunnel_process:
            logger.info("Stopping Cloudflare tunnel...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            self.tunnel_process = None
            self.tunnel_url = None

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure tunnel is stopped when exiting context"""
        self.stop() 