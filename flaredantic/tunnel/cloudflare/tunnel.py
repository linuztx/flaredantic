import subprocess
import threading
from typing import Union, Optional
from ...base.tunnel import BaseTunnel
from ...exceptions import TunnelError
from ...logging_config import setup_logger, GREEN, RESET
from .config import FlareConfig
from .downloader import FlareDownloader

class FlareTunnel(BaseTunnel):
    def __init__(self, config: Union[FlareConfig, dict]):
        """
        Initialize FlareTunnel with configuration
        
        Args:
            config: FlareConfig object or dict with configuration parameters
        """
        super().__init__()
        if isinstance(config, dict):
            self.config = FlareConfig(**config)
        else:
            self.config = config
            
        self.tunnel_process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        
        # Initialize logger and ensure bin directory exists
        self.logger = setup_logger(self.config.verbose)
        self.config.bin_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Using binary directory: {self.config.bin_dir}")

    def _extract_tunnel_url(self, process: subprocess.Popen) -> None:
        """Extract tunnel URL from cloudflared output"""
        self.logger.debug("Starting tunnel URL extraction...")
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break

            line = line if isinstance(line, str) else line.decode('utf-8')
            if "trycloudflare.com" in line and "https://" in line:
                if "api.trycloudflare.com" in line:
                    self.logger.debug("Skipping api.trycloudflare.com URL")
                    continue
                start = line.find("https://")
                end = line.find("trycloudflare.com") + len("trycloudflare.com")
                self.tunnel_url = line[start:end].strip()
                self.logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                return

    def start(self) -> str:
        """
        Start the cloudflare tunnel
        
        Returns:
            Tunnel URL once available
        """
        if not self.binary_path:
            self.logger.debug("No cloudflared binary found, downloading...")
            downloader = FlareDownloader(self.config.bin_dir, self.config.verbose)
            self.binary_path = downloader.download()

        self.logger.info(f"Starting Cloudflare tunnel on port {self.config.port}...")
        try:
            self.tunnel_process = subprocess.Popen(
                [
                    str(self.binary_path),
                    "tunnel",
                    "--url",
                    f"http://localhost:{self.config.port}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )
            self.logger.debug("Tunnel process started")

            url_thread = threading.Thread(
                target=self._extract_tunnel_url,
                args=(self.tunnel_process,),
                daemon=True
            )
            url_thread.start()
            self.logger.debug(f"Waiting for tunnel URL (timeout: {self.config.timeout}s)...")
            url_thread.join(timeout=self.config.timeout)

            if not self.tunnel_url:
                self.logger.error("Timeout waiting for tunnel URL")
                raise TunnelError("Timeout waiting for tunnel URL")

            return self.tunnel_url

        except Exception as e:
            self.logger.error(f"Failed to start tunnel: {str(e)}")
            self.stop()
            raise TunnelError(f"Failed to start tunnel: {str(e)}") from e

    def stop(self) -> None:
        """Stop the cloudflare tunnel"""
        self._stop_event.set()
        if self.tunnel_process:
            self.logger.info("Stopping Cloudflare tunnel...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            self.tunnel_process = None
            self.tunnel_url = None
            self.logger.debug("Tunnel stopped successfully") 