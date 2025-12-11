"""Base protocol adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, Callable


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the broker/server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""
        pass

    @abstractmethod
    async def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        """Publish a message to a topic."""
        pass

    @abstractmethod
    async def subscribe(
        self, topic: str, callback: Callable[[str, Any], None], qos: int = 1
    ) -> None:
        """Subscribe to a topic with a callback."""
        pass

    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the adapter is connected."""
        pass

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Get the protocol name."""
        pass
