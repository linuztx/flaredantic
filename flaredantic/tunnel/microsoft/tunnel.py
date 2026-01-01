import subprocess
import threading
import re
from typing import Union, Optional
from ...base.tunnel import BaseTunnel
from ...core.exceptions import MicrosoftTunnelError
from ...core.logging_config import setup_logger, GREEN, RESET
from ...core.notify import NotifyEvent
from .config import MicrosoftConfig
from .downloader import MicrosoftDownloader


class MicrosoftTunnel(BaseTunnel):
    """
    Microsoft Dev Tunnel implementation
    """
    def __init__(self, config: Union[MicrosoftConfig, dict]):
        """
        Initialize Microsoft Tunnel

        Args:
            config: MicrosoftConfig object or dict with configuration
        """
        super().__init__()
        if isinstance(config, dict):
            self.config = MicrosoftConfig(**config)
        else:
            self.config = config

        self.tunnel_process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()

        self.logger = setup_logger(self.config.verbose)
        self.config.bin_dir.mkdir(parents=True, exist_ok=True)

    def _run_cmd(self, args):
        cmd = [str(self.binary_path)] + args  # type: ignore
        self.logger.debug(f"Running: {' '.join(cmd)}")
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def _ensure_logged_in(self) -> None:
        """
        Ensure user is logged in to Microsoft Dev Tunnel.
        Handles device login flow if not logged in.
        """
        # Check login status
        result = self._run_cmd(["user", "show"])
        if result.returncode == 0 and "Logged in as" in result.stdout:
            self.logger.debug("User already logged in to Microsoft Dev Tunnels")
            self.notify(NotifyEvent.INFO, "Already logged in to Microsoft Dev Tunnels")
            return

        # Trigger device login and stream output to capture device code promptly
        login_args = ["user", "login"]
        # Always default to GitHub device login
        login_args += ["-g"]
        login_args += ["-d"] if self.config.device_login else []

        cmd = [str(self.binary_path)] + login_args  # type: ignore
        self.logger.debug(f"Running: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        code_announced = False
        for raw_line in iter(proc.stdout.readline, ''):
            line = raw_line.strip()
            if not line:
                continue
            # Try to extract device code and URL as soon as they appear
            if not code_announced:
                url_match = re.search(r"https?://\S+", line)
                code_match = re.search(r"code:\s*([A-Z0-9-]{4,})", line)
                if url_match and code_match:
                    self.logger.info(f"Browse to {url_match.group(0)} and enter the code: {GREEN}{code_match.group(1)}{RESET}")
                    self.notify(NotifyEvent.INFO, f"Login required: {url_match.group(0)} - Code: {code_match.group(1)}", {
                        "url": url_match.group(0),
                        "code": code_match.group(1)
                    })
                    code_announced = True
                elif url_match:
                    self.logger.info(f"Login required. Open: {GREEN}{url_match.group(0)}{RESET}")
                    self.notify(NotifyEvent.INFO, f"Login required: {url_match.group(0)}", {"url": url_match.group(0)})
                    code_announced = True
            # Echo informative lines when verbose
            if self.config.verbose:
                self.logger.debug(line)
        proc.wait()

        # Re-check login status
        result = self._run_cmd(["user", "show"])
        if result.returncode != 0 or "Logged in as" not in result.stdout:
            self.notify(NotifyEvent.ERROR, "Microsoft Dev Tunnels login failed or not completed")
            raise MicrosoftTunnelError("Microsoft Dev Tunnels login failed or not completed")

    def _ensure_tunnel(self) -> None:
        """
        Ensure tunnel and port are created
        """
        # Create tunnel if it doesn't exist
        show = self._run_cmd(["show", self.config.tunnel_id])
        if show.returncode != 0:
            create = self._run_cmd(["create", self.config.tunnel_id])
            if create.returncode != 0:
                raise MicrosoftTunnelError(f"Failed to create tunnel: {create.stdout}")

        # Ensure port exists
        port_show = self._run_cmd(["port", "show", self.config.tunnel_id, "-p", str(self.config.port)])
        if port_show.returncode != 0:
            port_create = self._run_cmd([
                "port", "create", self.config.tunnel_id,
                "-p", str(self.config.port),
                "--protocol", "http"
            ])
            if port_create.returncode != 0:
                raise MicrosoftTunnelError(f"Failed to create port: {port_create.stdout}")

    def _extract_urls_from_line(self, line: str) -> Optional[str]:
        """
        Extract tunnel URL from a line of output
        """
        if line.startswith("Connect via browser:"):
            parts = line.split(":", 1)[1].strip()
            urls = [u.strip() for u in parts.split(",")]
            return urls[-1] if urls else None
        return None

    def _extract_tunnel_url(self, process: subprocess.Popen) -> None:
        """
        Extract tunnel URL from process output
        """
        self.logger.debug("Starting Microsoft Dev Tunnels URL extraction...")
        if process.stdout is None:
            self.logger.error("Process stdout is not available")
            return
        current_hosting_port: Optional[int] = None
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break
            line = line if isinstance(line, str) else line.decode('utf-8')
            stripped = line.strip()

            # Track which port the following URLs correspond to
            if stripped.startswith("Hosting port:"):
                try:
                    current_hosting_port = int(stripped.split(":", 1)[1].strip())
                except Exception:
                    current_hosting_port = None
                continue

            # Capture only the URL for the requested port
            if current_hosting_port == self.config.port:
                url = self._extract_urls_from_line(stripped)
                if url:
                    self.tunnel_url = url
                    self.logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                    return

    def start(self) -> str:
        """
        Start the Microsoft Dev Tunnels

        Returns:
            Tunnel URL
        
        Raises:
            MicrosoftTunnelError: If tunnel fails to start
        """
        if not self.binary_path:
            downloader = MicrosoftDownloader(self.config.bin_dir, self.config.verbose)
            self.binary_path = downloader.download()

        self._ensure_logged_in()
        self._ensure_tunnel()

        self.notify(NotifyEvent.CREATING_TUNNEL, f"Starting Microsoft Dev Tunnels on port {self.config.port}...")
        self.logger.info(f"Starting Microsoft Dev Tunnels tunnel on port {self.config.port}...")

        try:
            # Start hosting process and extract URL asynchronously
            self.tunnel_process = subprocess.Popen(
                [str(self.binary_path), "host", self.config.tunnel_id, "--allow-anonymous"],  # type: ignore
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
            self.logger.debug(f"Waiting for tunnel URL (timeout: {self.config.timeout}s)...")
            url_thread.join(timeout=self.config.timeout)

            if not self.tunnel_url:
                self.notify(NotifyEvent.ERROR, "Timeout waiting for Microsoft Dev Tunnels URL")
                raise MicrosoftTunnelError("Timeout waiting for Microsoft Dev Tunnels URL")

            self.notify(NotifyEvent.TUNNEL_URL, self.tunnel_url, {"url": self.tunnel_url})
            return self.tunnel_url
        except Exception as e:
            self.logger.error(f"Failed to start Microsoft Dev Tunnels: {str(e)}")
            self.notify(NotifyEvent.ERROR, f"Failed to start Microsoft Dev Tunnels: {str(e)}")
            self.stop()
            raise MicrosoftTunnelError(f"Failed to start Microsoft Dev Tunnels: {str(e)}") from e

    def stop(self) -> None:
        """
        Stop the Microsoft Dev Tunnels
        """
        self._stop_event.set()
        if self.tunnel_process:
            self.logger.info("Stopping Microsoft Dev Tunnels host...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            self.tunnel_process = None
            self.tunnel_url = None
            self.notify(NotifyEvent.TUNNEL_STOPPED, "Microsoft Dev Tunnels stopped")
