import json
import os
import platform
import re
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional, Union
from urllib.parse import urlparse
from ...base.tunnel import BaseTunnel
from ...core.exceptions import TailscaleDownloadError, TailscaleTunnelError
from ...core.logging_config import setup_logger, GREEN, RESET
from ...core.notify import NotifyEvent
from ...utils.tailscale import find_tailscale
from .config import TailscaleConfig
from .downloader import TailscaleDownloader

# Socket of the tailscaled run by flaredantic. It is relative to the state dir
# (the working directory of every command) so the path never exceeds the
# ~108 byte limit of Unix socket paths.
SOCKET_NAME = "tailscaled.sock"


class TailscaleTunnel(BaseTunnel):
    """
    Tailscale Funnel implementation
    """
    def __init__(self, config: Union[TailscaleConfig, dict]):
        """
        Initialize Tailscale Funnel

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
        self._stop_event = threading.Event()
        self._managed = False
        self._state_dir = Path(self.config.state_dir).expanduser().resolve()
        self._daemon_output: Deque[str] = deque(maxlen=20)
        self._daemon_reader: Optional[threading.Thread] = None
        self._action_url: Optional[str] = None

        self.logger = setup_logger(self.config.verbose)

    @property
    def _cwd(self) -> Optional[Path]:
        """Working directory for tailscale commands"""
        return self._state_dir if self._managed else None

    def _cmd(self, args: List[str]) -> List[str]:
        """Build a tailscale command for the daemon in use"""
        socket_args = [f"--socket={SOCKET_NAME}"] if self._managed else []
        return [str(self.binary_path)] + socket_args + args

    def _popen(self, args: List[str]) -> subprocess.Popen:
        """Start a tailscale command with its output piped back"""
        cmd = self._cmd(args)
        shown = [re.sub(r"^(--auth-key=).+", r"\1***", arg) for arg in cmd]
        self.logger.debug(f"Running: {' '.join(shown)}")
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            cwd=self._cwd,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

    def _status(self) -> Optional[dict]:
        """
        Get tailscaled status

        Returns:
            Status, or None if tailscaled can't be reached
        """
        try:
            result = subprocess.run(
                self._cmd(["status", "--json", "--peers=false"]),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Keep CLI warnings out of the JSON
                stdin=subprocess.DEVNULL,
                cwd=self._cwd,
                timeout=10
            )
            if result.returncode != 0:
                return None
            return json.loads(result.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return None

    def _wait_for_backend(self) -> dict:
        """
        Wait for tailscaled to finish starting up

        Returns:
            tailscaled status
        """
        deadline = time.time() + self.config.timeout
        while True:
            if self.daemon_process and self.daemon_process.poll() is not None:
                if self._daemon_reader:
                    self._daemon_reader.join(timeout=1)
                raise TailscaleTunnelError(f"tailscaled exited: {' '.join(list(self._daemon_output)[-3:])}")
            status = self._status()
            if status and status.get("BackendState") not in ("NoState", "Starting"):
                return status
            if time.time() > deadline:
                raise TailscaleTunnelError("Timeout waiting for tailscaled to start")
            time.sleep(0.5)

    def _read_output(self, process: subprocess.Popen, output: List[str]) -> None:
        """
        Read tailscale command output, announcing the URLs the user has to
        open (login, machine approval, enabling Funnel) and capturing the
        Funnel URL
        """
        if process.stdout is None:
            self.logger.error("Process stdout is not available")
            return
        public = False
        context: List[str] = []
        while not self._stop_event.is_set():
            line = process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            output.append(line)
            self.logger.debug(line)

            if line.startswith("Available on the internet"):
                public = True
                continue
            url_match = re.search(r"https://\S+", line)
            if not url_match:
                context.append(line)
                continue

            url = url_match.group(0).rstrip(".,;")
            if public or (urlparse(url).hostname or "").endswith(".ts.net"):
                self.tunnel_url = url.rstrip("/")
                self.logger.info(f"Tunnel URL: {GREEN}{self.tunnel_url}{RESET}")
                return

            # URLs are printed on their own line after what they are for
            message = " ".join(context[-2:] + [url]) if line == url_match.group(0) else line
            context = []
            self._action_url = url
            self.logger.info(message.replace(url, f"{GREEN}{url}{RESET}"))
            self.notify(NotifyEvent.INFO, message, {"url": url})

    def _read_daemon_output(self, process: subprocess.Popen) -> None:
        """
        Keep reading tailscaled logs so its output pipe never fills up
        """
        if process.stdout is None:
            return
        for line in iter(process.stdout.readline, ''):
            self._daemon_output.append(line.strip())

    def _connect(self) -> None:
        """
        Connect to a Tailscale node that is logged in and running.
        Uses the Tailscale running on this machine when available, otherwise
        runs a separate userspace tailscaled managed by flaredantic (Linux only).
        """
        self._managed = False
        if self.config.use_system:
            self.binary_path = find_tailscale()
            if self.binary_path and self._status() is not None:
                self._use_system_tailscale()
                return

        if platform.system().lower() != "linux":
            raise TailscaleTunnelError(
                "Tailscale is not running. Install it from https://tailscale.com/download "
                "and log in (flaredantic can only run its own Tailscale node on Linux)"
            )
        self._start_daemon()
        self._login()

    def _use_system_tailscale(self) -> None:
        """
        Use the Tailscale running on this machine. It is never logged in or
        brought up here, as that could change the user's own network settings.
        """
        status = self._wait_for_backend()
        state = status.get("BackendState")
        if state != "Running":
            raise TailscaleTunnelError(
                f"Tailscale is not connected (state: {state}). "
                "Run 'tailscale up' or connect from the Tailscale app, then try again"
            )
        self.logger.info("Using the Tailscale running on this machine")
        self.notify(NotifyEvent.INFO, "Using the Tailscale running on this machine")

    def _start_daemon(self) -> None:
        """
        Start a userspace tailscaled with its own state, separate from any
        Tailscale installed on this machine
        """
        self.config.bin_dir.mkdir(parents=True, exist_ok=True)
        downloader = TailscaleDownloader(self.config.bin_dir, self.config.verbose)
        self.binary_path = downloader.download().resolve()
        self._managed = True

        self._state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        # tailscaled removes its socket on exit, so only a leftover one needs checking
        if (self._state_dir / SOCKET_NAME).exists() and self._status() is not None:
            raise TailscaleTunnelError(
                f"A Tailscale node started by flaredantic is already running from {self._state_dir}"
            )

        self.logger.info("Starting a Tailscale node managed by flaredantic...")
        self.notify(NotifyEvent.INFO, "Starting a Tailscale node managed by flaredantic...")
        env = os.environ.copy()
        env["TS_LOGS_DIR"] = str(self._state_dir)  # Keep tailscaled logs out of /var/lib/tailscale
        self.daemon_process = subprocess.Popen(
            [
                str(self.binary_path.with_name("tailscaled")),
                "--tun=userspace-networking",
                f"--statedir={self._state_dir}",
                f"--socket={SOCKET_NAME}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            cwd=self._state_dir,
            env=env,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        self._daemon_output.clear()
        self._daemon_reader = threading.Thread(
            target=self._read_daemon_output,
            args=(self.daemon_process,),
            daemon=True
        )
        self._daemon_reader.start()

    def _login(self) -> None:
        """
        Log in the node managed by flaredantic. Shows a login URL to open
        unless an auth key is configured.
        """
        status = self._wait_for_backend()
        args = ["up", f"--hostname={self.config.hostname}"]
        if status.get("BackendState") == "Running":
            self.logger.debug("Already logged in to Tailscale")
            self.notify(NotifyEvent.INFO, "Already logged in to Tailscale")
        elif self.config.auth_key:
            args.append(f"--auth-key={self.config.auth_key}")

        output: List[str] = []
        process = self._popen(args)
        reader = threading.Thread(target=self._read_output, args=(process, output), daemon=True)
        reader.start()
        try:
            process.wait(timeout=self.config.login_timeout)
        except subprocess.TimeoutExpired:
            raise TailscaleTunnelError("Timeout waiting for Tailscale login")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
        reader.join(timeout=1)
        if process.returncode != 0:
            raise TailscaleTunnelError("\n".join(output) or "Tailscale login failed")

    def start(self) -> str:
        """
        Start the Tailscale Funnel

        Returns:
            Tunnel URL

        Raises:
            TailscaleDownloadError: If the Tailscale binaries can't be downloaded
            TailscaleTunnelError: If tunnel fails to start
        """
        self._stop_event.clear()
        try:
            self._connect()

            self.notify(NotifyEvent.CREATING_TUNNEL, f"Starting Tailscale Funnel on port {self.config.port}...")
            self.logger.info(f"Starting Tailscale Funnel on port {self.config.port}...")

            # Runs in the foreground: tailscaled removes the Funnel when this process exits
            self.tunnel_url = None
            self._action_url = None
            output: List[str] = []
            self.tunnel_process = self._popen([
                "funnel",
                f"--https={self.config.https_port}",
                f"http://localhost:{self.config.port}"
            ])

            url_thread = threading.Thread(
                target=self._read_output,
                args=(self.tunnel_process, output),
                daemon=True
            )
            url_thread.start()
            self.logger.debug(f"Waiting for tunnel URL (timeout: {self.config.timeout}s)...")
            url_thread.join(timeout=self.config.timeout)
            if url_thread.is_alive() and self._action_url:
                # Funnel is waiting to be enabled for the tailnet in the browser
                url_thread.join(timeout=self.config.login_timeout)

            if not self.tunnel_url:
                if url_thread.is_alive():
                    raise TailscaleTunnelError("Timeout waiting for Tailscale Funnel URL")
                raise TailscaleTunnelError("\n".join(output) or "tailscale funnel exited unexpectedly")

            self.notify(NotifyEvent.TUNNEL_URL, self.tunnel_url, {"url": self.tunnel_url})
            return self.tunnel_url
        except TailscaleDownloadError:
            self.stop()
            raise
        except Exception as e:
            self.logger.error(f"Failed to start Tailscale Funnel: {str(e)}")
            self.notify(NotifyEvent.ERROR, f"Failed to start Tailscale Funnel: {str(e)}")
            self.stop()
            raise TailscaleTunnelError(f"Failed to start Tailscale Funnel: {str(e)}") from e
        except BaseException:
            # e.g. Ctrl+C while waiting for login: don't leave tailscaled running
            self.stop()
            raise

    def stop(self) -> None:
        """
        Stop the Tailscale Funnel
        """
        self._stop_event.set()
        if self.tunnel_process:
            self.logger.info("Stopping Tailscale Funnel...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            self.tunnel_process = None
            self.tunnel_url = None
            self.notify(NotifyEvent.TUNNEL_STOPPED, "Tailscale Funnel stopped")
        if self.daemon_process:
            self.logger.debug("Stopping tailscaled...")
            self.daemon_process.terminate()
            try:
                self.daemon_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.daemon_process.kill()
                self.daemon_process.wait()
            self.daemon_process = None
