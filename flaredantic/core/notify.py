from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass
import threading


class NotifyEvent(Enum):
    """Event types for tunnel notifications"""
    DOWNLOADING = "downloading"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETE = "download_complete"
    CREATING_TUNNEL = "creating_tunnel"
    TUNNEL_URL = "tunnel_url"
    TUNNEL_STOPPED = "tunnel_stopped"
    ERROR = "error"
    INFO = "info"


@dataclass
class NotifyData:
    """Data payload for notification events"""
    event: NotifyEvent
    message: str
    data: Optional[Any] = None


# Type alias for callback functions
NotifyCallback = Callable[[NotifyData], None]


class Notifier:
    """
    Manages notification callbacks for tunnel events.
    Thread-safe singleton pattern.
    """
    _instance: Optional["Notifier"] = None
    _lock = threading.Lock()
    _callbacks: list[NotifyCallback]

    def __new__(cls) -> "Notifier":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._callbacks = []
                    cls._instance = instance
        return cls._instance

    def subscribe(self, callback: NotifyCallback) -> None:
        """Subscribe a callback to receive notifications"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: NotifyCallback) -> None:
        """Unsubscribe a callback from notifications"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def notify(self, event: NotifyEvent, message: str, data: Optional[Any] = None) -> None:
        """Emit a notification to all subscribers"""
        notify_data = NotifyData(event=event, message=message, data=data)
        for callback in self._callbacks:
            try:
                callback(notify_data)
            except Exception:
                pass  # Don't let callback errors break the tunnel

    def clear(self) -> None:
        """Clear all subscribers"""
        self._callbacks.clear()


# Global notifier instance
notifier = Notifier()

