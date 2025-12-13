"""Metrics writer for InfluxDB."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

from .config import settings

logger = logging.getLogger(__name__)


class MetricsWriter:
    """Writes device metrics to InfluxDB."""

    def __init__(self):
        self.settings = settings
        self._client: InfluxDBClient | None = None
        self._write_api = None
        self._enabled = bool(self.settings.influxdb_url and self.settings.influxdb_token)

    async def connect(self) -> None:
        """Connect to InfluxDB."""
        if not self._enabled:
            logger.warning("InfluxDB not configured, metrics disabled")
            return

        try:
            self._client = InfluxDBClient(
                url=self.settings.influxdb_url,
                token=self.settings.influxdb_token,
                org=self.settings.influxdb_org,
            )
            self._write_api = self._client.write_api(write_options=ASYNCHRONOUS)
            logger.info(f"Connected to InfluxDB at {self.settings.influxdb_url}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self._enabled = False

    async def close(self) -> None:
        """Close InfluxDB connection."""
        if self._write_api:
            self._write_api.close()
        if self._client:
            self._client.close()

    def write_telemetry(
        self,
        device_id: str,
        model_id: str,
        data: dict[str, Any],
        group_id: str | None = None,
    ) -> None:
        """Write telemetry data point to InfluxDB.

        Args:
            device_id: Device identifier
            model_id: Device model identifier
            data: Telemetry data as key-value pairs
            group_id: Optional device group identifier
        """
        if not self._enabled or not self._write_api:
            return

        try:
            point = (
                Point("telemetry")
                .tag("device_id", device_id)
                .tag("model_id", model_id)
                .time(datetime.now(timezone.utc))
            )

            if group_id:
                point = point.tag("group_id", group_id)

            for key, value in data.items():
                if key in ("deviceId", "timestamp"):
                    continue
                if isinstance(value, (int, float)):
                    point = point.field(key, float(value))
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    point = point.field(key, value)

            self._write_api.write(
                bucket=self.settings.influxdb_bucket,
                record=point,
            )
        except Exception as e:
            logger.warning(f"Failed to write telemetry metric: {e}")

    def write_device_event(
        self,
        device_id: str,
        event_type: str,
        model_id: str,
        group_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Write device lifecycle event to InfluxDB.

        Args:
            device_id: Device identifier
            event_type: Event type (created, started, stopped, deleted)
            model_id: Device model identifier
            group_id: Optional device group identifier
            metadata: Optional event metadata
        """
        if not self._enabled or not self._write_api:
            return

        try:
            point = (
                Point("device_events")
                .tag("device_id", device_id)
                .tag("model_id", model_id)
                .tag("event_type", event_type)
                .field("value", 1)
                .time(datetime.now(timezone.utc))
            )

            if group_id:
                point = point.tag("group_id", group_id)

            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, float(value))
                    elif isinstance(value, str):
                        point = point.field(f"meta_{key}", value)

            self._write_api.write(
                bucket=self.settings.influxdb_bucket,
                record=point,
            )
        except Exception as e:
            logger.warning(f"Failed to write device event metric: {e}")

    def write_engine_stats(
        self,
        active_devices: int,
        total_messages: int,
        total_bytes: int,
        active_groups: int,
    ) -> None:
        """Write engine statistics to InfluxDB.

        Args:
            active_devices: Number of active devices
            total_messages: Total messages sent
            total_bytes: Total bytes sent
            active_groups: Number of active device groups
        """
        if not self._enabled or not self._write_api:
            return

        try:
            point = (
                Point("engine_stats")
                .field("active_devices", active_devices)
                .field("total_messages", total_messages)
                .field("total_bytes", total_bytes)
                .field("active_groups", active_groups)
                .time(datetime.now(timezone.utc))
            )

            self._write_api.write(
                bucket=self.settings.influxdb_bucket,
                record=point,
            )
        except Exception as e:
            logger.warning(f"Failed to write engine stats: {e}")

    def write_connection_metric(
        self,
        device_id: str,
        protocol: str,
        connected: bool,
        latency_ms: float | None = None,
    ) -> None:
        """Write connection metric to InfluxDB.

        Args:
            device_id: Device identifier
            protocol: Protocol name (mqtt, coap, http)
            connected: Whether device is connected
            latency_ms: Optional connection latency in milliseconds
        """
        if not self._enabled or not self._write_api:
            return

        try:
            point = (
                Point("connections")
                .tag("device_id", device_id)
                .tag("protocol", protocol)
                .field("connected", connected)
                .time(datetime.now(timezone.utc))
            )

            if latency_ms is not None:
                point = point.field("latency_ms", latency_ms)

            self._write_api.write(
                bucket=self.settings.influxdb_bucket,
                record=point,
            )
        except Exception as e:
            logger.warning(f"Failed to write connection metric: {e}")


# Global metrics writer instance
_metrics_writer: MetricsWriter | None = None


def get_metrics_writer() -> MetricsWriter:
    """Get the global metrics writer instance."""
    global _metrics_writer
    if _metrics_writer is None:
        _metrics_writer = MetricsWriter()
    return _metrics_writer


async def init_metrics() -> None:
    """Initialize the metrics writer."""
    writer = get_metrics_writer()
    await writer.connect()


async def close_metrics() -> None:
    """Close the metrics writer."""
    global _metrics_writer
    if _metrics_writer:
        await _metrics_writer.close()
        _metrics_writer = None
