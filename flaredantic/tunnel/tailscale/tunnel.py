import json
import os
import platform
import shutil
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Union, Optional, List
from ...base.tunnel import BaseTunnel
from ...core.exceptions import TailscaleTunnelError
from ...core.logging_config import setup_logger, GREEN, RESET
from ...core.notify import NotifyEvent
from .config import TailscaleConfig
from .downloader import TailscaleDownloader

# Where the Tailscale apps put their CLI when it is not on PATH
SYSTEM_CLI_PATHS = {
    "darwin": Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale"),
    "windows": Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale" / "tailscale.exe",
}

# Socket of the private tailscaled, relative to its directory
SOCKET_NAME = "tailscaled.sock"


class TailscaleTunnel(BaseTunnel):
    """
    Tailscale Funnel implementation
    """
    def __init__(self, config: Union[TailscaleConfig, dict]):
        """
        Initialize Tailscale Tunnel

        Args:
            config: TailscaleConfig object or dict with configuration
        """
        super().__init__()
        if isinstance(config, dict):
            self.config = TailscaleConfig(**config)
        else:
            self.config = config

        self.tunnel_process: Optional[subprocess.Popen] = None
        self.daemon_process: Optional[subprocess.Popen] = None
        self._login_process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._enable_url: Optional[str] = None
        self._last_output: deque = deque(maxlen=5)

        # On Linux a private tailscaled is run in userspace mode (no root needed),
        # elsewhere the installed Tailscale app is used
        self._managed = not self.config.use_system and platform.system().lower() == "linux"
        self._home = self.config.bin_dir.resolve() / "tailscale"
        # Commands run from there so the socket path can stay relative
        # (Unix socket paths are limited to about 107 bytes)
        self._cwd = str(self._home) if self._managed else None

        self.logger = setup_logger(self.config.verbose)
        self.config.bin_dir.mkdir(parents=True, exist_ok=True)

    def _cmd(self, *args: str) -> List[str]:
        """
        Build a tailscale CLI command, pointed at the private daemon if there is one
        """
        cmd = [str(self.binary_path)]
        if self._managed:
            cmd.append(f"--socket={SOCKET_NAME}")
        return cmd + list(args)

    def _popen(self, *args: str) -> subprocess.Popen:
        """
        Start a tailscale CLI command with its output piped line by line
        """
        cmd = self._cmd(*args)
        # Keep the auth key out of the logs
        shown = ["--authkey=***" if arg.startswith("--authkey=") else arg for arg in cmd]
        self.logger.debug(f"Running: {' '.join(shown)}")
        return subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
            cwd=self._cwd
        )

    def _status(self) -> Optional[dict]:
        """
        Get the local node status, or None if tailscaled is not reachable
        """
        try:
            result = subprocess.run(
                self._cmd("status", "--json", "--peers=false"),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                cwd=self._cwd
            )
            return json.loads(result.stdout) if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, ValueError):
            return None

    def _backend_state(self) -> Optional[str]:
        """
        Get the backend state (e.g. NeedsLogin, Running), or None if tailscaled is not reachable
        """
        status = self._status()
        return status.get("BackendState") if status else None

    def _find_system_cli(self) -> Path:
        """
        Find the CLI of the installed Tailscale app

        Raises:
            TailscaleTunnelError: If Tailscale is not installed
        """
        cli = shutil.which("tailscale")
        if cli:
            return Path(cli)
        candidate = SYSTEM_CLI_PATHS.get(platform.system().lower())
        if candidate and candidate.exists():
            return candidate
        self.logger.error("Tailscale is not installed")
        self.notify(NotifyEvent.ERROR, "Tailscale is not installed")
        raise TailscaleTunnelError("Tailscale is not installed. Install it from https://tailscale.com/download and try again.")

    def _ensure_daemon(self) -> None:
        """
        Ensure tailscaled is reachable, starting the private one if needed
        """
        if self._status() is not None:
            self.logger.debug("Using running tailscaled")
            return
        if not self._managed:
            raise TailscaleTunnelError("Tailscale is not running. Start Tailscale and try again.")

        state_dir = self._home / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._home / "tailscaled.log"
        cmd = [
            str(self._home / "tailscaled"),
            "--tun=userspace-networking",
            f"--statedir={state_dir}",
            f"--socket={SOCKET_NAME}",
            "--port=0"
        ]
        self.logger.debug(f"Running: {' '.join(cmd)}")
        with open(log_path, "w") as log_file:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=self._cwd,
                # Keep its log buffers out of any system-wide Tailscale directory
                env=dict(os.environ, TS_LOGS_DIR=str(state_dir))
            )
        self.daemon_process = process

        # Wait until it has loaded its state, so the login step sees the real one
        deadline = time.time() + self.config.timeout
        while self._backend_state() in (None, "NoState"):
            if process.poll() is not None:
                raise TailscaleTunnelError(f"tailscaled exited unexpectedly, see {log_path}")
            if time.time() > deadline:
                raise TailscaleTunnelError(f"Timeout waiting for tailscaled to start, see {log_path}")
            time.sleep(0.5)

    def _ensure_logged_in(self) -> None:
        """
        Ensure the node is logged in to Tailscale.
        Handles the login flow (browser URL or auth key) if not logged in.
        """
        state = self._backend_state()
        if state == "Running":
            self.logger.debug("Already logged in to Tailscale")
            self.notify(NotifyEvent.INFO, "Already logged in to Tailscale")
            if not self._managed:
                return  # Leave the settings of the user's own install alone

        login_args = ["up"]
        if self._managed:
            # The private daemon is ours, so keep its settings in line with the config
            login_args += ["--reset", f"--hostname={self.config.hostname}"]
        auth_key = self.config.auth_key or os.environ.get("TS_AUTHKEY")
        if auth_key and state == "NeedsLogin":
            # Only for an actual login: passing a key makes "up" re-authenticate the node
            login_args.append(f"--authkey={auth_key}")

        proc = self._popen(*login_args)
        self._login_process = proc
        assert proc.stdout is not None
        output: deque = deque(maxlen=5)
        for raw_line in iter(proc.stdout.readline, ''):
            line = raw_line.strip()
            if not line:
                continue
            self.logger.debug(line)
            if line.startswith("https://"):
                self.logger.info(f"Login required. Open: {GREEN}{line}{RESET}")
                self.notify(NotifyEvent.INFO, f"Login required: {line}", {"url": line})
                output.clear()  # Only keep what comes after the prompt for errors
            else:
                output.append(line)
        proc.wait()

        if self._backend_state() != "Running":
            message = "Tailscale login failed or not completed"
            reason = " ".join(output)
            raise TailscaleTunnelError(f"{message}: {reason}" if reason else message)

    def _extract_tunnel_url(self, process: subprocess.Popen) -> None:
        """
        Extract tunnel URL from process output
        """
        self.logger.debug("Starting Tailscale Funnel URL extraction...")
        if process.stdout is None:
            self.logger.error("Process stdout is not available")
            return
        available = False
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break
            stripped = line.strip()
            if not stripped:
                continue
            self.logger.debug(stripped)

            # The public URL is listed under "Available on the internet:"
            if stripped.startswith("Available on the internet"):
                available = True
            elif stripped.startswith("https://") and available:
                self.tunnel_url = stripped.rstrip("/")
                self.logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                return
            elif stripped.startswith("https://"):
                # Any URL before that is where Funnel has to be enabled for the tailnet
                self._enable_url = stripped
                self.logger.info(f"Funnel is not enabled for your tailnet. Open: {GREEN}{stripped}{RESET}")
                self.notify(NotifyEvent.INFO, f"Enable Tailscale Funnel: {stripped}", {"url": stripped})
            else:
                self._last_output.append(stripped)

    @staticmethod
    def _terminate(process: subprocess.Popen) -> None:
        """
        Terminate a process, killing it if it does not exit in time
        """
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def start(self) -> str:
        """
        Start Tailscale Funnel

        Returns:
            Tunnel URL

        Raises:
            TailscaleDownloadError: If the binaries fail to download
            TailscaleTunnelError: If tunnel fails to start
        """
        self._stop_event.clear()
        self._enable_url = None
        self._last_output.clear()

        if not self.binary_path:
            if self._managed:
                # Private, as it holds the node keys and login URLs
                self._home.mkdir(mode=0o700, parents=True, exist_ok=True)
                downloader = TailscaleDownloader(self._home, self.config.verbose)
                self.binary_path = downloader.download()
            else:
                self.binary_path = self._find_system_cli()

        try:
            self._ensure_daemon()
            self._ensure_logged_in()

            self.notify(NotifyEvent.CREATING_TUNNEL, f"Starting Tailscale Funnel on port {self.config.port}...")
            self.logger.info(f"Starting Tailscale Funnel on port {self.config.port}...")

            # Foreground mode: the Funnel config is removed again when the process exits
            self.tunnel_process = self._popen("funnel", f"http://localhost:{self.config.port}")

            url_thread = threading.Thread(
                target=self._extract_tunnel_url,
                args=(self.tunnel_process,),
                daemon=True
            )
            url_thread.start()
            self.logger.debug(f"Waiting for tunnel URL (timeout: {self.config.timeout}s)...")
            url_thread.join(timeout=self.config.timeout)
            # Enabling Funnel happens in the browser, so wait for the user like the login does
            while url_thread.is_alive() and self._enable_url and not self._stop_event.is_set():
                url_thread.join(timeout=1)

            if not self.tunnel_url:
                if url_thread.is_alive():
                    reason = "Timeout waiting for Tailscale Funnel URL"
                elif self._enable_url:
                    reason = f"Tailscale Funnel is not enabled for your tailnet. Enable it at {self._enable_url} and try again"
                else:
                    reason = " ".join(self._last_output) or "tailscale funnel exited unexpectedly"
                raise TailscaleTunnelError(reason)

            self.notify(NotifyEvent.TUNNEL_URL, self.tunnel_url, {"url": self.tunnel_url})
            return self.tunnel_url
        except Exception as e:
            self.logger.error(f"Failed to start Tailscale Funnel: {str(e)}")
            self.notify(NotifyEvent.ERROR, f"Failed to start Tailscale Funnel: {str(e)}")
            self.stop()
            raise TailscaleTunnelError(f"Failed to start Tailscale Funnel: {str(e)}") from e
        except BaseException:
            # e.g. Ctrl+C while waiting for the login, don't leave tailscaled running
            self.stop()
            raise

    def stop(self) -> None:
        """
        Stop Tailscale Funnel, and the private tailscaled if it was started here
        """
        self._stop_event.set()
        # Take each process before stopping it: stop() may also be running in
        # another thread while start() cleans up after a failure
        login_process, self._login_process = self._login_process, None
        if login_process:
            self._terminate(login_process)
        tunnel_process, self.tunnel_process = self.tunnel_process, None
        if tunnel_process:
            self.logger.info("Stopping Tailscale Funnel...")
            self._terminate(tunnel_process)
            self.tunnel_url = None
            self.notify(NotifyEvent.TUNNEL_STOPPED, "Tailscale Funnel stopped")
        daemon_process, self.daemon_process = self.daemon_process, None
        if daemon_process:
            self.logger.debug("Stopping tailscaled...")
            self._terminate(daemon_process)
