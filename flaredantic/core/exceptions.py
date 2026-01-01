class CloudflaredError(Exception):
    """Base exception for cloudflared-related errors"""
    pass

class DownloadError(CloudflaredError):
    """Raised when cloudflared binary download fails"""
    pass

class TunnelError(CloudflaredError):
    """Raised when tunnel operations fail"""
    pass

class ServeoError(Exception):
    """Base exception for Serveo-related errors"""
    pass

class SSHError(ServeoError):
    """Raised when SSH operations for Serveo fail"""
    pass

class MicrosoftError(Exception):
    """Base exception for Microsoft-related errors"""
    pass

class MicrosoftDownloadError(MicrosoftError):
    """Raised when Microsoft Dev Tunnels binary download fails"""
    pass

class MicrosoftTunnelError(MicrosoftError):
    """Raised when Microsoft Dev Tunnels tunnel operations fail"""
    pass