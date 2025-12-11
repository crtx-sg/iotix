"""HTTP protocol adapter using aiohttp."""

import json
import logging
from typing import Any, Callable

import aiohttp

from .base import ProtocolAdapter

logger = logging.getLogger(__name__)


class HttpAdapter(ProtocolAdapter):
    """HTTP protocol adapter implementation."""

    def __init__(
        self,
        client_id: str,
        base_url: str,
        use_tls: bool = False,
        headers: dict[str, str] | None = None,
        auth: tuple[str, str] | None = None,
    ):
        self.client_id = client_id
        self.base_url = base_url.rstrip("/")
        self.use_tls = use_tls
        self.headers = headers or {}
        self.auth = auth

        self._session: aiohttp.ClientSession | None = None
        self._connected = False

    async def connect(self) -> None:
        """Create HTTP client session."""
        auth = None
        if self.auth:
            auth = aiohttp.BasicAuth(self.auth[0], self.auth[1])

        self._session = aiohttp.ClientSession(
            headers=self.headers,
            auth=auth,
        )
        self._connected = True
        logger.info(f"HTTP session created for {self.base_url}")

    async def disconnect(self) -> None:
        """Close HTTP client session."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False

    async def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        """Send HTTP POST request to publish data."""
        if not self._session:
            raise ConnectionError("HTTP session not initialized")

        url = f"{self.base_url}/{topic}"

        if isinstance(payload, (dict, list)):
            async with self._session.post(url, json=payload) as response:
                if not response.ok:
                    text = await response.text()
                    raise RuntimeError(f"HTTP POST failed: {response.status} - {text}")
        else:
            async with self._session.post(url, data=payload) as response:
                if not response.ok:
                    text = await response.text()
                    raise RuntimeError(f"HTTP POST failed: {response.status} - {text}")

    async def subscribe(
        self, topic: str, callback: Callable[[str, Any], None], qos: int = 1
    ) -> None:
        """
        Subscribe to HTTP endpoint via polling.

        Note: HTTP doesn't have native pub/sub support.
        This implementation uses polling as a simple approach.
        For real-time updates, consider using WebSockets or SSE.
        """
        logger.warning(
            f"HTTP subscribe is polling-based. Topic: {topic}. "
            "Consider using WebSockets for real-time updates."
        )

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from HTTP polling."""
        pass

    def is_connected(self) -> bool:
        """Check if HTTP session is active."""
        return self._connected and self._session is not None

    @property
    def protocol_name(self) -> str:
        """Get the protocol name."""
        return "http"

    async def get(self, topic: str) -> Any:
        """Send HTTP GET request."""
        if not self._session:
            raise ConnectionError("HTTP session not initialized")

        url = f"{self.base_url}/{topic}"
        async with self._session.get(url) as response:
            if not response.ok:
                text = await response.text()
                raise RuntimeError(f"HTTP GET failed: {response.status} - {text}")

            content_type = response.content_type
            if "json" in content_type:
                return await response.json()
            return await response.text()

    async def put(self, topic: str, payload: Any) -> Any:
        """Send HTTP PUT request."""
        if not self._session:
            raise ConnectionError("HTTP session not initialized")

        url = f"{self.base_url}/{topic}"

        if isinstance(payload, (dict, list)):
            async with self._session.put(url, json=payload) as response:
                if not response.ok:
                    text = await response.text()
                    raise RuntimeError(f"HTTP PUT failed: {response.status} - {text}")
                return await response.json() if response.content_type == "application/json" else await response.text()
        else:
            async with self._session.put(url, data=payload) as response:
                if not response.ok:
                    text = await response.text()
                    raise RuntimeError(f"HTTP PUT failed: {response.status} - {text}")
                return await response.text()
