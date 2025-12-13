from typing import Optional, Union, Literal
from enum import Enum
import threading

from .tunnel.cloudflare import FlareTunnel, FlareConfig
from .tunnel.serveo import ServeoTunnel, ServeoConfig
from .tunnel.microsoft import MicrosoftTunnel, MicrosoftConfig
from .base.tunnel import BaseTunnel
from .core.notify import notifier, NotifyCallback, NotifyEvent, NotifyData


class TunnelProvider(Enum):
    """Supported tunnel providers"""
    CLOUDFLARE = "cloudflare"
    SERVEO = "serveo"
    MICROSOFT = "microsoft"


class TunnelManager:
    """
    Singleton manager for tunnel operations.
    Provides a unified interface for creating and managing tunnels
    with notification support for frontend integration.
    """
    _instance: Optional["TunnelManager"] = None
    _lock = threading.Lock()
    _tunnel: Optional[BaseTunnel]
    _provider: Optional[TunnelProvider]

    def __new__(cls) -> "TunnelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._tunnel = None
                    instance._provider = None
                    cls._instance = instance
        return cls._instance

    @property
    def tunnel(self) -> Optional[BaseTunnel]:
        """Get the current tunnel instance"""
        return self._tunnel

    @property
    def tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL"""
        return self._tunnel.tunnel_url if self._tunnel else None

    @property
    def provider(self) -> Optional[TunnelProvider]:
        """Get the current provider"""
        return self._provider

    @property
    def is_running(self) -> bool:
        """Check if a tunnel is currently running"""
        return self._tunnel is not None and self._tunnel.tunnel_url is not None

    def subscribe(self, callback: NotifyCallback) -> None:
        """Subscribe to tunnel notifications"""
        notifier.subscribe(callback)

    def unsubscribe(self, callback: NotifyCallback) -> None:
        """Unsubscribe from tunnel notifications"""
        notifier.unsubscribe(callback)

    def create_tunnel(
        self,
        provider: Union[TunnelProvider, Literal["cloudflare", "serveo", "microsoft"]],
        config: Union[FlareConfig, ServeoConfig, MicrosoftConfig, dict]
    ) -> str:
        """
        Create and start a tunnel.

        Args:
            provider: The tunnel provider to use
            config: Configuration for the tunnel (provider-specific config or dict)

        Returns:
            The tunnel URL

        Raises:
            ValueError: If provider is not supported
            TunnelError: If tunnel creation fails
        """
        # Stop existing tunnel if any
        if self._tunnel:
            self.stop()

        # Normalize provider
        if isinstance(provider, str):
            provider = TunnelProvider(provider)

        self._provider = provider

        # Create appropriate tunnel based on provider
        if provider == TunnelProvider.CLOUDFLARE:
            self._tunnel = FlareTunnel(config)  # type: ignore[arg-type]
        elif provider == TunnelProvider.SERVEO:
            self._tunnel = ServeoTunnel(config)  # type: ignore[arg-type]
        elif provider == TunnelProvider.MICROSOFT:
            self._tunnel = MicrosoftTunnel(config)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return self._tunnel.start()

    def stop(self) -> None:
        """Stop the current tunnel"""
        if self._tunnel:
            self._tunnel.stop()
            self._tunnel = None
            self._provider = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Global singleton instance
tunnel_manager = TunnelManager()

