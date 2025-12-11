"""CoAP protocol adapter using aiocoap."""

import json
import logging
from typing import Any, Callable

from .base import ProtocolAdapter

logger = logging.getLogger(__name__)


class CoapAdapter(ProtocolAdapter):
    """CoAP protocol adapter implementation."""

    def __init__(
        self,
        client_id: str,
        server_host: str,
        server_port: int = 5683,
        use_dtls: bool = False,
    ):
        self.client_id = client_id
        self.server_host = server_host
        self.server_port = server_port
        self.use_dtls = use_dtls

        self._context = None
        self._connected = False
        self._observations: dict[str, Any] = {}

    async def connect(self) -> None:
        """Initialize CoAP context."""
        try:
            import aiocoap

            self._context = await aiocoap.Context.create_client_context()
            self._connected = True
            logger.info(f"CoAP context created for {self.server_host}:{self.server_port}")
        except ImportError:
            raise RuntimeError("aiocoap is required for CoAP support")
        except Exception as e:
            raise ConnectionError(f"Failed to create CoAP context: {e}")

    async def disconnect(self) -> None:
        """Shutdown CoAP context."""
        if self._context:
            await self._context.shutdown()
            self._context = None
        self._connected = False

    async def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        """Send a CoAP PUT request to publish data."""
        import aiocoap

        if not self._context:
            raise ConnectionError("CoAP context not initialized")

        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            payload = payload.encode("utf-8")

        uri = f"coap://{self.server_host}:{self.server_port}/{topic}"
        request = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload)

        if qos >= 1:
            request.mtype = aiocoap.CON
        else:
            request.mtype = aiocoap.NON

        response = await self._context.request(request).response

        if not response.code.is_successful():
            raise RuntimeError(f"CoAP PUT failed: {response.code}")

    async def subscribe(
        self, topic: str, callback: Callable[[str, Any], None], qos: int = 1
    ) -> None:
        """Observe a CoAP resource."""
        import aiocoap

        if not self._context:
            raise ConnectionError("CoAP context not initialized")

        uri = f"coap://{self.server_host}:{self.server_port}/{topic}"
        request = aiocoap.Message(code=aiocoap.GET, uri=uri, observe=0)

        observation = self._context.request(request)
        self._observations[topic] = observation

        async def observe_loop():
            async for response in observation.observation:
                try:
                    payload = json.loads(response.payload.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = response.payload
                callback(topic, payload)

        import asyncio

        asyncio.create_task(observe_loop())

    async def unsubscribe(self, topic: str) -> None:
        """Cancel observation of a CoAP resource."""
        if topic in self._observations:
            observation = self._observations.pop(topic)
            observation.observation.cancel()

    def is_connected(self) -> bool:
        """Check if CoAP context is active."""
        return self._connected

    @property
    def protocol_name(self) -> str:
        """Get the protocol name."""
        return "coap"
