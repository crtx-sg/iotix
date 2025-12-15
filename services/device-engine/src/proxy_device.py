"""Proxy device implementation for forwarding external device telemetry."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

from .metrics import get_metrics_writer
from .models import (
    BindingConfig,
    BindingStatus,
    DeviceModelConfig,
    DeviceStatus,
    ConnectionState,
    Protocol,
)

logger = logging.getLogger(__name__)


class ProxyDevice:
    """Proxy device that forwards external telemetry to InfluxDB."""

    def __init__(
        self,
        device_id: str,
        model: DeviceModelConfig,
        group_id: str | None = None,
    ):
        self.device_id = device_id
        self.model = model
        self.group_id = group_id

        # State
        self.status = DeviceStatus.CREATED
        self.connection_state = ConnectionState.DISCONNECTED
        self.created_at = datetime.now(timezone.utc)
        self.bound_at: datetime | None = None
        self.last_telemetry_at: datetime | None = None
        self.error_message: str | None = None

        # Binding
        self.binding: BindingConfig | None = None
        self._adapter: Any = None

        # Metrics (received, not generated)
        self.messages_received = 0
        self.bytes_received = 0
        self.error_count = 0

        # Webhook URL (set when bound via HTTP)
        self.webhook_url: str | None = None

    async def bind(self, config: BindingConfig) -> str | None:
        """Bind to external device source.

        Args:
            config: Binding configuration

        Returns:
            Webhook URL if HTTP protocol, None otherwise
        """
        if self.status == DeviceStatus.RUNNING:
            raise RuntimeError("Device already bound")

        self.status = DeviceStatus.STARTING
        self.error_message = None
        metrics_writer = get_metrics_writer()

        try:
            # Create protocol-specific adapter
            self._adapter = self._create_adapter(config)

            self.connection_state = ConnectionState.CONNECTING
            connect_start = datetime.now(timezone.utc)

            # Start the adapter
            webhook_url = await self._adapter.bind(self._on_telemetry)

            connect_latency = (datetime.now(timezone.utc) - connect_start).total_seconds() * 1000
            self.connection_state = ConnectionState.CONNECTED

            # Write connection metric
            metrics_writer.write_connection_metric(
                device_id=self.device_id,
                protocol=config.protocol.value,
                connected=True,
                latency_ms=connect_latency,
                source="physical",
            )

            self.binding = config
            self.bound_at = datetime.now(timezone.utc)
            self.status = DeviceStatus.RUNNING
            self.webhook_url = webhook_url

            # Write device bound event
            metrics_writer.write_device_event(
                device_id=self.device_id,
                event_type="bound",
                model_id=self.model.id,
                group_id=self.group_id,
                source="physical",
            )

            logger.info(f"Proxy device {self.device_id} bound to {config.protocol.value}")
            return webhook_url

        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.connection_state = ConnectionState.DISCONNECTED
            self.error_message = str(e)
            self.error_count += 1

            metrics_writer.write_connection_metric(
                device_id=self.device_id,
                protocol=config.protocol.value,
                connected=False,
                source="physical",
            )

            logger.error(f"Failed to bind proxy device {self.device_id}: {e}")
            raise

    async def unbind(self) -> None:
        """Unbind from external device source."""
        if self.status == DeviceStatus.STOPPED:
            return

        self.status = DeviceStatus.STOPPING
        metrics_writer = get_metrics_writer()

        if self._adapter:
            try:
                await self._adapter.unbind()
            except Exception as e:
                logger.warning(f"Error unbinding proxy device {self.device_id}: {e}")
            self._adapter = None

        protocol = self.binding.protocol.value if self.binding else "unknown"
        self.connection_state = ConnectionState.DISCONNECTED
        self.status = DeviceStatus.STOPPED
        self.binding = None
        self.webhook_url = None

        # Write connection metric
        metrics_writer.write_connection_metric(
            device_id=self.device_id,
            protocol=protocol,
            connected=False,
            source="physical",
        )

        # Write device unbound event
        metrics_writer.write_device_event(
            device_id=self.device_id,
            event_type="unbound",
            model_id=self.model.id,
            group_id=self.group_id,
            source="physical",
        )

        logger.info(f"Proxy device {self.device_id} unbound")

    def _create_adapter(self, config: BindingConfig) -> Any:
        """Create protocol-specific proxy adapter."""
        if config.protocol == Protocol.MQTT:
            from .adapters.mqtt_proxy import MqttProxyAdapter
            return MqttProxyAdapter(
                device_id=self.device_id,
                broker=config.broker or "localhost",
                port=config.port or 1883,
                topic=config.topic or f"devices/{self.device_id}/telemetry",
                qos=config.qos,
                username=config.username,
            )
        elif config.protocol == Protocol.HTTP:
            from .adapters.http_proxy import HttpProxyAdapter
            return HttpProxyAdapter(
                device_id=self.device_id,
                webhook_path=config.webhook_path,
            )
        else:
            raise ValueError(f"Unsupported proxy protocol: {config.protocol}")

    async def _on_telemetry(self, payload: dict[str, Any]) -> None:
        """Handle incoming telemetry from adapter - passthrough to InfluxDB.

        Args:
            payload: Telemetry data from external device
        """
        self.messages_received += 1
        self.bytes_received += len(json.dumps(payload))
        self.last_telemetry_at = datetime.now(timezone.utc)

        # Write to InfluxDB with source="physical" tag
        metrics_writer = get_metrics_writer()
        metrics_writer.write_telemetry(
            device_id=self.device_id,
            model_id=self.model.id,
            data=payload,
            group_id=self.group_id,
            source="physical",
        )

    def get_binding_status(self) -> BindingStatus:
        """Get current binding status."""
        if not self.binding:
            return BindingStatus(bound=False)

        return BindingStatus(
            bound=True,
            protocol=self.binding.protocol,
            broker=self.binding.broker,
            port=self.binding.port,
            topic=self.binding.topic,
            webhook_url=self.webhook_url,
            resource_uri=self.binding.resource_uri,
            bound_at=self.bound_at,
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get device metrics."""
        return {
            "deviceId": self.device_id,
            "messagesSent": 0,  # Proxy devices don't send
            "messagesReceived": self.messages_received,
            "bytesSent": 0,
            "bytesReceived": self.bytes_received,
            "connectionCount": 1 if self.connection_state == ConnectionState.CONNECTED else 0,
            "errorCount": self.error_count,
            "lastTelemetry": None,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert device state to dictionary."""
        result = {
            "id": self.device_id,
            "modelId": self.model.id,
            "type": "proxy",
            "status": self.status.value,
            "connectionState": self.connection_state.value,
            "createdAt": self.created_at.isoformat(),
            "boundAt": self.bound_at.isoformat() if self.bound_at else None,
            "lastTelemetryAt": self.last_telemetry_at.isoformat() if self.last_telemetry_at else None,
            "errorMessage": self.error_message,
            "groupId": self.group_id,
            "binding": self.get_binding_status().model_dump(by_alias=True) if self.binding else None,
        }
        return result
