"""Virtual device implementation."""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .adapters.base import ProtocolAdapter
from .adapters.mqtt import MqttAdapter
from .adapters.http import HttpAdapter
from .generators import create_generator, ValueGenerator
from .metrics import get_metrics_writer
from .models import (
    ConnectionConfig,
    DeviceModelConfig,
    DeviceStatus,
    ConnectionState,
    TelemetryAttributeConfig,
)

logger = logging.getLogger(__name__)


class VirtualDevice:
    """Virtual IoT device that generates telemetry and handles commands."""

    def __init__(
        self,
        device_id: str,
        model: DeviceModelConfig,
        connection_override: ConnectionConfig | None = None,
        group_id: str | None = None,
    ):
        self.device_id = device_id
        self.model = model
        self.group_id = group_id

        # Merge connection config
        self.connection = self._merge_connection(
            model.connection, connection_override
        )

        # State
        self.status = DeviceStatus.CREATED
        self.connection_state = ConnectionState.DISCONNECTED
        self.created_at = datetime.now(timezone.utc)
        self.started_at: datetime | None = None
        self.last_telemetry_at: datetime | None = None
        self.error_message: str | None = None

        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.error_count = 0

        # Internal state
        self._adapter: ProtocolAdapter | None = None
        self._generators: dict[str, ValueGenerator] = {}
        self._telemetry_tasks: list[asyncio.Task] = []
        self._running = False
        self._last_telemetry: dict[str, Any] = {}
        self._custom_state: dict[str, Any] = {}

        # Initialize generators
        self._init_generators()

    def _merge_connection(
        self,
        base: ConnectionConfig | None,
        override: ConnectionConfig | None,
    ) -> ConnectionConfig:
        """Merge base and override connection configs."""
        if not base:
            base = ConnectionConfig()
        if not override:
            return base

        return ConnectionConfig(
            broker=override.broker or base.broker,
            port=override.port or base.port,
            tls=override.tls if override.tls is not None else base.tls,
            client_id_pattern=override.client_id_pattern or base.client_id_pattern,
            topic_pattern=override.topic_pattern or base.topic_pattern,
            qos=override.qos if override.qos is not None else base.qos,
            keep_alive=override.keep_alive if override.keep_alive else base.keep_alive,
            clean_session=override.clean_session if override.clean_session is not None else base.clean_session,
            username=override.username or base.username,
            password_ref=override.password_ref or base.password_ref,
        )

    def _init_generators(self) -> None:
        """Initialize telemetry generators."""
        for attr in self.model.telemetry:
            self._generators[attr.name] = create_generator(attr.generator)

    def _resolve_template(self, template: str) -> str:
        """Resolve template variables in strings."""
        replacements = {
            "${deviceId}": self.device_id,
            "${timestamp}": datetime.now(timezone.utc).isoformat(),
            "${modelId}": self.model.id,
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, str(value))

        # Resolve custom state variables
        for key, value in self._custom_state.items():
            result = result.replace(f"${{{key}}}", str(value))

        # Resolve last telemetry values
        for key, value in self._last_telemetry.items():
            result = result.replace(f"${{{key}}}", str(value))

        return result

    def _create_adapter(self) -> ProtocolAdapter:
        """Create protocol adapter based on model configuration."""
        protocol = self.model.protocol.value
        client_id = self._resolve_template(
            self.connection.client_id_pattern or f"iotix-{self.device_id}"
        )

        if protocol == "mqtt":
            return MqttAdapter(
                client_id=client_id,
                broker_host=self.connection.broker or "localhost",
                broker_port=self.connection.port or 1883,
                use_tls=self.connection.tls,
                username=self.connection.username,
                password=None,  # TODO: resolve from secrets
                keep_alive=self.connection.keep_alive,
                clean_session=self.connection.clean_session,
            )
        elif protocol == "http":
            base_url = f"{'https' if self.connection.tls else 'http'}://{self.connection.broker}:{self.connection.port or 80}"
            return HttpAdapter(
                client_id=client_id,
                base_url=base_url,
                use_tls=self.connection.tls,
            )
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    async def start(self) -> None:
        """Start the virtual device."""
        if self.status == DeviceStatus.RUNNING:
            return

        self.status = DeviceStatus.STARTING
        self.error_message = None
        metrics_writer = get_metrics_writer()

        try:
            # Create and connect adapter
            self._adapter = self._create_adapter()
            self.connection_state = ConnectionState.CONNECTING

            connect_start = datetime.now(timezone.utc)
            await self._adapter.connect()
            connect_latency = (datetime.now(timezone.utc) - connect_start).total_seconds() * 1000

            self.connection_state = ConnectionState.CONNECTED

            # Write connection metric
            metrics_writer.write_connection_metric(
                device_id=self.device_id,
                protocol=self.model.protocol.value,
                connected=True,
                latency_ms=connect_latency,
            )

            # Start telemetry generation
            self._running = True
            self.started_at = datetime.now(timezone.utc)
            self._start_telemetry_tasks()

            self.status = DeviceStatus.RUNNING

            # Write device started event
            metrics_writer.write_device_event(
                device_id=self.device_id,
                event_type="started",
                model_id=self.model.id,
                group_id=self.group_id,
            )

            logger.info(f"Device {self.device_id} started")

        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.connection_state = ConnectionState.DISCONNECTED
            self.error_message = str(e)
            self.error_count += 1

            # Write connection failure metric
            metrics_writer.write_connection_metric(
                device_id=self.device_id,
                protocol=self.model.protocol.value,
                connected=False,
            )

            logger.error(f"Failed to start device {self.device_id}: {e}")
            raise

    async def stop(self) -> None:
        """Stop the virtual device."""
        if self.status == DeviceStatus.STOPPED:
            return

        self.status = DeviceStatus.STOPPING
        self._running = False
        metrics_writer = get_metrics_writer()

        # Cancel telemetry tasks
        for task in self._telemetry_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._telemetry_tasks.clear()

        # Disconnect adapter
        if self._adapter:
            try:
                await self._adapter.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting device {self.device_id}: {e}")
            self._adapter = None

        self.connection_state = ConnectionState.DISCONNECTED
        self.status = DeviceStatus.STOPPED

        # Write connection metric (disconnected)
        metrics_writer.write_connection_metric(
            device_id=self.device_id,
            protocol=self.model.protocol.value,
            connected=False,
        )

        # Write device stopped event
        metrics_writer.write_device_event(
            device_id=self.device_id,
            event_type="stopped",
            model_id=self.model.id,
            group_id=self.group_id,
        )

        logger.info(f"Device {self.device_id} stopped")

    def _start_telemetry_tasks(self) -> None:
        """Start async tasks for telemetry generation."""
        for attr in self.model.telemetry:
            task = asyncio.create_task(self._telemetry_loop(attr))
            self._telemetry_tasks.append(task)

    async def _telemetry_loop(self, attr: TelemetryAttributeConfig) -> None:
        """Generate and publish telemetry for an attribute."""
        generator = self._generators.get(attr.name)
        if not generator:
            return

        interval_seconds = attr.interval_ms / 1000.0
        topic_pattern = attr.topic or self.connection.topic_pattern or f"devices/{self.device_id}/telemetry"
        topic = self._resolve_template(topic_pattern)

        while self._running:
            try:
                # Generate value
                value = generator.generate()
                self._last_telemetry[attr.name] = value

                # Build payload
                payload = {
                    "deviceId": self.device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    attr.name: value,
                }
                if attr.unit:
                    payload["unit"] = attr.unit

                # Publish
                if self._adapter and self._adapter.is_connected():
                    await self._adapter.publish(topic, payload, self.connection.qos)
                    self.messages_sent += 1
                    self.bytes_sent += len(json.dumps(payload))
                    self.last_telemetry_at = datetime.now(timezone.utc)

                    # Write to InfluxDB
                    metrics_writer = get_metrics_writer()
                    metrics_writer.write_telemetry(
                        device_id=self.device_id,
                        model_id=self.model.id,
                        data=payload,
                        group_id=self.group_id,
                    )

                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telemetry error for {self.device_id}.{attr.name}: {e}")
                self.error_count += 1
                await asyncio.sleep(interval_seconds)

    def get_metrics(self) -> dict[str, Any]:
        """Get device metrics."""
        return {
            "deviceId": self.device_id,
            "messagesSent": self.messages_sent,
            "messagesReceived": self.messages_received,
            "bytesSent": self.bytes_sent,
            "bytesReceived": self.bytes_received,
            "connectionCount": 1 if self.connection_state == ConnectionState.CONNECTED else 0,
            "errorCount": self.error_count,
            "lastTelemetry": self._last_telemetry,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert device state to dictionary."""
        return {
            "id": self.device_id,
            "modelId": self.model.id,
            "status": self.status.value,
            "connectionState": self.connection_state.value,
            "createdAt": self.created_at.isoformat(),
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "lastTelemetryAt": self.last_telemetry_at.isoformat() if self.last_telemetry_at else None,
            "errorMessage": self.error_message,
            "groupId": self.group_id,
        }
