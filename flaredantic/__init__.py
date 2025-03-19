from .tunnel.cloudflare import FlareTunnel, FlareConfig
from .tunnel.serveo import ServeoTunnel, ServeoConfig
from .core.exceptions import (
    CloudflaredError,
    DownloadError,
    TunnelError,
    ServeoError,
    SSHError
)
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

    # Exceptions
    "CloudflaredError",
    "DownloadError",
    "TunnelError",
    "ServeoError",
    "SSHError",

    # Version
    "__version__",
]