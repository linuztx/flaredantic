import subprocess
import threading
import os
from typing import Union, Optional
from ...base.tunnel import BaseTunnel
from ...core.exceptions import TunnelError, ServeoError, SSHError
from ...core.logging_config import setup_logger, GREEN, RESET
from .config import ServeoConfig
from ...utils.serveo import is_serveo_up
from ...utils.ssh import is_ssh_installed

class ServeoTunnel(BaseTunnel):
    def __init__(self, config: Union[ServeoConfig, dict]) -> None:
        """
        Initialize ServeoTunnel with configuration

        Args:
            config: ServeoConfig object or dict with configuration parameters
        """
        super().__init__()
        if isinstance(config, dict):
            self.config = ServeoConfig(**config)
        else:
            self.config = config

        self.tunnel_process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()

        # Initialize logger
        self.logger = setup_logger(self.config.verbose) 

    def _extract_tunnel_url(self, process: subprocess.Popen) -> None:
        """Extract tunnel URL from serveo output"""
        self.logger.debug("Starting tunnel URL extraction...")
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break

            line = line.strip() if isinstance(line, str) else line.decode().strip()
            
            # Handle TCP port allocation
            if self.config.tcp and "Allocated port" in line:
                port = line.split("Allocated port")[1].split()[0]
                self.tunnel_url = f"serveo.net:{port}"
                self.logger.info(f"TCP tunnel available at: {GREEN}{self.tunnel_url}{RESET}")
                return
                
            # Handle HTTP URL detection
            elif not self.config.tcp and "serveo.net" in line and "https://" in line:
                start = line.find("https://")
                end = line.find(".serveo.net") + len(".serveo.net")
                self.tunnel_url = line[start:end].strip()
                self.logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                return
    
    def start(self) -> str:
        """
        Start the serveo tunnel

        Returns:
            Tunnel URL once available
        """
        self.logger.info(f"Starting Serveo tunnel on port {self.config.port}...")
        
        # Check for SSH client first
        if not is_ssh_installed():
            self.logger.error("SSH client is not installed - required for Serveo tunnels")
            raise SSHError("SSH client is not installed. Install OpenSSH and try again.")

        # Then check Serveo availability
        if not is_serveo_up():
            self.logger.error("Serveo server is currently unavailable")
            raise ServeoError("Serveo server is currently down")

        try:
            self.config.ssh_dir.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env["Home"] = str(self.config.ssh_dir)

            port_mapping = "0" if self.config.tcp else "80"
            
            cmd = [
                "ssh",
                "-T",
                "-R", f"{port_mapping}:localhost:{self.config.port}",
                "-o", f"UserKnownHostsFile={self.config.known_host_file}",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "ServerAliveInterval=60",  # Keep connection alive
                "-o", "ExitOnForwardFailure=yes",  # Exit if port forwarding fails
                "serveo.net"
            ]

            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                env=env
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
                raise ServeoError("Timeout waiting for tunnel URL")
            
            return self.tunnel_url
        
        except Exception as e:
            self.logger.error(f"Failed to start tunnel: {str(e)}")
            self.stop()
            raise ServeoError(f"Failed to start tunnel: {str(e)}") from e

    def stop(self) -> None:
        """Stop the serveo tunnel"""
        self._stop_event.set()
        if self.tunnel_process:
            self.logger.info("Stopping Serveo tunnel...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            self.tunnel_process = None
            self.tunnel_url = None
            self.logger.debug("Tunnel stopped successfully") 