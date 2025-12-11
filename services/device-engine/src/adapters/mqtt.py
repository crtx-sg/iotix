"""MQTT protocol adapter using paho-mqtt."""

import asyncio
import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt

from .base import ProtocolAdapter

logger = logging.getLogger(__name__)


class MqttAdapter(ProtocolAdapter):
    """MQTT protocol adapter implementation."""

    def __init__(
        self,
        client_id: str,
        broker_host: str,
        broker_port: int = 1883,
        use_tls: bool = False,
        username: str | None = None,
        password: str | None = None,
        keep_alive: int = 60,
        clean_session: bool = True,
    ):
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.use_tls = use_tls
        self.username = username
        self.password = password
        self.keep_alive = keep_alive
        self.clean_session = clean_session

        self._client: mqtt.Client | None = None
        self._connected = False
        self._subscriptions: dict[str, Callable[[str, Any], None]] = {}
        self._connect_event = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self) -> None:
        """Connect to the MQTT broker."""
        self._loop = asyncio.get_event_loop()
        self._connect_event.clear()

        self._client = mqtt.Client(
            client_id=self.client_id,
            clean_session=self.clean_session,
            protocol=mqtt.MQTTv311,
        )

        if self.username:
            self._client.username_pw_set(self.username, self.password)

        if self.use_tls:
            self._client.tls_set()

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._client.connect_async(
            self.broker_host, self.broker_port, self.keep_alive
        )
        self._client.loop_start()

        # Wait for connection with timeout
        try:
            await asyncio.wait_for(self._connect_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            raise ConnectionError(
                f"Timeout connecting to MQTT broker at {self.broker_host}:{self.broker_port}"
            )

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            self._client = None

    async def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        """Publish a message to a topic."""
        if not self._client or not self._connected:
            raise ConnectionError("Not connected to MQTT broker")

        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        result = self._client.publish(topic, payload, qos=qos)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Failed to publish message: {mqtt.error_string(result.rc)}")

    async def subscribe(
        self, topic: str, callback: Callable[[str, Any], None], qos: int = 1
    ) -> None:
        """Subscribe to a topic with a callback."""
        if not self._client or not self._connected:
            raise ConnectionError("Not connected to MQTT broker")

        self._subscriptions[topic] = callback
        result, _ = self._client.subscribe(topic, qos=qos)

        if result != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Failed to subscribe to {topic}")

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        if not self._client:
            return

        self._client.unsubscribe(topic)
        self._subscriptions.pop(topic, None)

    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected

    @property
    def protocol_name(self) -> str:
        """Get the protocol name."""
        return "mqtt"

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict,
        rc: int,
    ) -> None:
        """Handle connection callback."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
            self._connected = True
            if self._loop:
                self._loop.call_soon_threadsafe(self._connect_event.set)
        else:
            logger.error(f"Failed to connect to MQTT broker: {mqtt.connack_string(rc)}")

    def _on_disconnect(
        self, client: mqtt.Client, userdata: Any, rc: int
    ) -> None:
        """Handle disconnection callback."""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {mqtt.error_string(rc)}")

    def _on_message(
        self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        """Handle incoming message callback."""
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = message.payload

        # Find matching subscription
        for pattern, callback in self._subscriptions.items():
            if self._topic_matches(pattern, topic):
                try:
                    callback(topic, payload)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern."""
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == "#":
                return True
            if i >= len(topic_parts):
                return False
            if pattern_part != "+" and pattern_part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts)
