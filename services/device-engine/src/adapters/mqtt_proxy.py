"""MQTT proxy adapter for subscribing to external device topics."""

import asyncio
import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttProxyAdapter:
    """MQTT adapter for proxying external device telemetry."""

    def __init__(
        self,
        device_id: str,
        broker: str,
        port: int,
        topic: str,
        qos: int = 1,
        username: str | None = None,
        password: str | None = None,
    ):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        self.topic = topic
        self.qos = qos
        self.username = username
        self.password = password

        self._client: mqtt.Client | None = None
        self._on_telemetry: Callable[[dict[str, Any]], Any] | None = None
        self._connected = False
        self._connect_event = asyncio.Event()

    async def bind(self, on_telemetry: Callable[[dict[str, Any]], Any]) -> str | None:
        """Bind to external MQTT topic.

        Args:
            on_telemetry: Callback function for received telemetry

        Returns:
            None (MQTT doesn't use webhook URLs)
        """
        self._on_telemetry = on_telemetry

        # Create MQTT client
        client_id = f"iotix-proxy-{self.device_id}"
        self._client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

        # Set callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Set credentials if provided
        if self.username:
            self._client.username_pw_set(self.username, self.password)

        # Connect
        self._client.connect_async(self.broker, self.port)
        self._client.loop_start()

        # Wait for connection
        try:
            await asyncio.wait_for(self._connect_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            self._client.loop_stop()
            raise RuntimeError(f"Timeout connecting to MQTT broker {self.broker}:{self.port}")

        if not self._connected:
            raise RuntimeError(f"Failed to connect to MQTT broker {self.broker}:{self.port}")

        logger.info(f"Proxy {self.device_id} subscribed to {self.topic}")
        return None

    async def unbind(self) -> None:
        """Unbind from external MQTT topic."""
        if self._client:
            try:
                self._client.unsubscribe(self.topic)
                self._client.disconnect()
                self._client.loop_stop()
            except Exception as e:
                logger.warning(f"Error during MQTT proxy unbind: {e}")
            finally:
                self._client = None
                self._connected = False
                self._connect_event.clear()

        logger.info(f"Proxy {self.device_id} unsubscribed from {self.topic}")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        """Handle MQTT connection."""
        if reason_code == mqtt.CONNACK_ACCEPTED:
            self._connected = True
            # Subscribe to the external topic
            client.subscribe(self.topic, self.qos)
            logger.info(f"Proxy connected and subscribed to {self.topic}")
        else:
            logger.error(f"Proxy MQTT connection failed: {reason_code}")
            self._connected = False

        self._connect_event.set()

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        """Handle MQTT disconnection."""
        self._connected = False
        logger.warning(f"Proxy MQTT disconnected: {reason_code}")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming MQTT message."""
        try:
            # Parse JSON payload
            payload = json.loads(message.payload.decode("utf-8"))

            # Call the telemetry callback
            if self._on_telemetry:
                # Run async callback in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._on_telemetry(payload))
                else:
                    loop.run_until_complete(self._on_telemetry(payload))

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse MQTT message as JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected
