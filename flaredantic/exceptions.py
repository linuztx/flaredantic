class CloudflaredError(Exception):
    """Base exception for cloudflared-related errors"""
    pass

class DownloadError(CloudflaredError):
    """Raised when cloudflared binary download fails"""
    pass

class TunnelError(CloudflaredError):
    """Raised when tunnel operations fail"""
    pass