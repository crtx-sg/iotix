"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    """Device type enumeration."""

    SENSOR = "sensor"
    GATEWAY = "gateway"
    ACTUATOR = "actuator"
    CUSTOM = "custom"


class Protocol(str, Enum):
    """Communication protocol enumeration."""

    MQTT = "mqtt"
    COAP = "coap"
    HTTP = "http"


class DeviceStatus(str, Enum):
    """Device lifecycle status."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ConnectionState(str, Enum):
    """Device connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class GeneratorType(str, Enum):
    """Telemetry value generator types."""

    RANDOM = "random"
    SEQUENCE = "sequence"
    REPLAY = "replay"
    CONSTANT = "constant"
    CUSTOM = "custom"


class Distribution(str, Enum):
    """Statistical distributions for random generator."""

    UNIFORM = "uniform"
    NORMAL = "normal"
    EXPONENTIAL = "exponential"


# Request/Response Models


class GeneratorConfig(BaseModel):
    """Configuration for a telemetry value generator."""

    type: GeneratorType
    min: float | None = None
    max: float | None = None
    distribution: Distribution = Distribution.UNIFORM
    mean: float | None = None
    stddev: float | None = None
    rate: float | None = None
    start: float | None = None
    step: float = 1.0
    wrap: bool = False
    value: Any | None = None
    data_file: str | None = Field(None, alias="dataFile")
    loop_replay: bool = Field(True, alias="loopReplay")
    handler: str | None = None
    params: dict[str, Any] | None = None


class TelemetryAttributeConfig(BaseModel):
    """Configuration for a telemetry attribute."""

    name: str
    type: str
    unit: str | None = None
    generator: GeneratorConfig
    interval_ms: int = Field(1000, alias="intervalMs")
    topic: str | None = None


class ConnectionConfig(BaseModel):
    """Connection configuration."""

    broker: str | None = None
    port: int | None = None
    tls: bool = False
    client_id_pattern: str | None = Field(None, alias="clientIdPattern")
    topic_pattern: str | None = Field(None, alias="topicPattern")
    qos: int = 1
    keep_alive: int = Field(60, alias="keepAlive")
    clean_session: bool = Field(True, alias="cleanSession")
    username: str | None = None
    password_ref: str | None = Field(None, alias="passwordRef")


class DeviceModelConfig(BaseModel):
    """Complete device model configuration."""

    id: str
    name: str
    description: str | None = None
    version: str = "1.0.0"
    type: DeviceType
    protocol: Protocol
    connection: ConnectionConfig | None = None
    telemetry: list[TelemetryAttributeConfig] = []
    metadata: dict[str, Any] | None = None


class DeviceInstance(BaseModel):
    """Device instance state representation."""

    id: str
    model_id: str = Field(alias="modelId")
    status: DeviceStatus
    connection_state: ConnectionState = Field(alias="connectionState")
    created_at: datetime = Field(alias="createdAt")
    started_at: datetime | None = Field(None, alias="startedAt")
    last_telemetry_at: datetime | None = Field(None, alias="lastTelemetryAt")
    error_message: str | None = Field(None, alias="errorMessage")
    group_id: str | None = Field(None, alias="groupId")

    model_config = {"populate_by_name": True}


class DeviceMetrics(BaseModel):
    """Device metrics response."""

    device_id: str = Field(alias="deviceId")
    messages_sent: int = Field(alias="messagesSent")
    messages_received: int = Field(alias="messagesReceived")
    bytes_sent: int = Field(alias="bytesSent")
    bytes_received: int = Field(alias="bytesReceived")
    connection_count: int = Field(alias="connectionCount")
    error_count: int = Field(alias="errorCount")
    last_telemetry: dict[str, Any] | None = Field(None, alias="lastTelemetry")

    model_config = {"populate_by_name": True}


class CreateDeviceRequest(BaseModel):
    """Request to create a device instance."""

    model_id: str = Field(alias="modelId")
    device_id: str | None = Field(None, alias="deviceId")
    group_id: str | None = Field(None, alias="groupId")
    override_connection: ConnectionConfig | None = Field(
        None, alias="overrideConnection"
    )


class CreateDeviceGroupRequest(BaseModel):
    """Request to create a device group."""

    model_id: str = Field(alias="modelId")
    count: int = Field(ge=1, le=100000)
    group_id: str | None = Field(None, alias="groupId")
    id_pattern: str = Field("device-{index}", alias="idPattern")
    stagger_ms: int = Field(0, alias="staggerMs")


class DeviceGroupResponse(BaseModel):
    """Response for device group operations."""

    group_id: str = Field(alias="groupId")
    device_count: int = Field(alias="deviceCount")
    devices_created: int = Field(alias="devicesCreated")
    devices_started: int = Field(alias="devicesStarted")
    devices_stopped: int = Field(alias="devicesStopped")
    status: str


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: list[Any]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    has_more: bool = Field(alias="hasMore")

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    uptime_seconds: float = Field(alias="uptimeSeconds")
    device_count: int = Field(alias="deviceCount")
    running_device_count: int = Field(alias="runningDeviceCount")

    model_config = {"populate_by_name": True}
