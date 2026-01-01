from .tunnel.cloudflare import FlareTunnel, FlareConfig
from .tunnel.serveo import ServeoTunnel, ServeoConfig
from .tunnel.microsoft import MicrosoftTunnel, MicrosoftConfig
from .core.exceptions import (
    CloudflaredError,
    DownloadError,
    TunnelError,
    ServeoError,
    SSHError
)
from .core.notify import (
    NotifyEvent,
    NotifyData,
    NotifyCallback,
    Notifier,
    notifier
)
from .tunnel_manager import TunnelManager, TunnelProvider, tunnel_manager
from .__version__ import __version__

# For backward compatibility
TunnelConfig = FlareConfig

__all__ = [
    # Cloudflare provider
    "FlareTunnel",
    "FlareConfig",
    "TunnelConfig",

    # Serveo provider
    "ServeoTunnel",
    "ServeoConfig",

    # Microsoft provider
    "MicrosoftTunnel",
    "MicrosoftConfig",

    # Tunnel Manager
    "TunnelManager",
    "TunnelProvider",
    "tunnel_manager",

    # Notification system
    "NotifyEvent",
    "NotifyData",
    "NotifyCallback",
    "Notifier",
    "notifier",

    # Exceptions
    "CloudflaredError",
    "DownloadError",
    "TunnelError",
    "ServeoError",
    "SSHError",

    # Version
    "__version__",
]
