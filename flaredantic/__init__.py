from .tunnel.cloudflare import FlareTunnel, FlareConfig
from .exceptions import (
    CloudflaredError,
    DownloadError,
    TunnelError
)
from .__version__ import __version__

# For backward compatibility
TunnelConfig = FlareConfig

__all__ = [
    # Cloudflare provider
    "FlareTunnel",
    "FlareConfig",
    "TunnelConfig",

    # Exceptions
    "CloudflaredError",
    "DownloadError",
    "TunnelError",

    # Version
    "__version__",
]