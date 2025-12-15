"""HTTP proxy adapter for receiving webhook telemetry from external devices."""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Global registry of webhook handlers
_webhook_handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}


def get_webhook_handler(device_id: str) -> Callable[[dict[str, Any]], Any] | None:
    """Get the webhook handler for a device.

    Args:
        device_id: Device identifier

    Returns:
        Handler callback or None if not registered
    """
    return _webhook_handlers.get(device_id)


def register_webhook_handler(device_id: str, handler: Callable[[dict[str, Any]], Any]) -> None:
    """Register a webhook handler for a device.

    Args:
        device_id: Device identifier
        handler: Callback function for received telemetry
    """
    _webhook_handlers[device_id] = handler
    logger.debug(f"Registered webhook handler for device {device_id}")


def unregister_webhook_handler(device_id: str) -> None:
    """Unregister a webhook handler for a device.

    Args:
        device_id: Device identifier
    """
    if device_id in _webhook_handlers:
        del _webhook_handlers[device_id]
        logger.debug(f"Unregistered webhook handler for device {device_id}")


class HttpProxyAdapter:
    """HTTP adapter for proxying external device telemetry via webhooks."""

    def __init__(
        self,
        device_id: str,
        webhook_path: str | None = None,
    ):
        self.device_id = device_id
        self.webhook_path = webhook_path or f"/api/v1/webhooks/{device_id}"
        self._on_telemetry: Callable[[dict[str, Any]], Any] | None = None

    async def bind(self, on_telemetry: Callable[[dict[str, Any]], Any]) -> str:
        """Bind to receive HTTP webhook POSTs.

        Args:
            on_telemetry: Callback function for received telemetry

        Returns:
            Webhook URL for external devices to POST to
        """
        self._on_telemetry = on_telemetry

        # Register the handler globally so FastAPI can route to it
        register_webhook_handler(self.device_id, on_telemetry)

        logger.info(f"Proxy {self.device_id} bound to webhook path {self.webhook_path}")
        return self.webhook_path

    async def unbind(self) -> None:
        """Unbind from HTTP webhook."""
        unregister_webhook_handler(self.device_id)
        self._on_telemetry = None
        logger.info(f"Proxy {self.device_id} unbound from webhook")
