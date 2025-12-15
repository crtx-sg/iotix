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
    PROXY = "proxy"


class DeviceSource(str, Enum):
    """Device source type for metrics tagging."""

    SIMULATED = "simulated"
    PHYSICAL = "physical"


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


class LaunchStrategy(str, Enum):
    """Device launch strategy enumeration."""

    IMMEDIATE = "immediate"  # All at once
    LINEAR = "linear"  # Fixed delay between each device
    BATCH = "batch"  # Launch in batches with delay between batches
    EXPONENTIAL = "exponential"  # Exponentially increasing delay


class LaunchConfig(BaseModel):
    """Configuration for device launch strategy."""

    strategy: LaunchStrategy = LaunchStrategy.IMMEDIATE
    delay_ms: int = Field(0, alias="delayMs", ge=0)  # Base delay in milliseconds
    batch_size: int = Field(100, alias="batchSize", ge=1)  # For batch strategy
    max_delay_ms: int = Field(60000, alias="maxDelayMs", ge=0)  # Cap for exponential
    exponent_base: float = Field(1.5, alias="exponentBase", ge=1.0)  # For exponential


class DropoutStrategy(str, Enum):
    """Device dropout/failure strategy enumeration."""

    IMMEDIATE = "immediate"  # All specified devices drop at once
    LINEAR = "linear"  # Fixed delay between each dropout
    EXPONENTIAL = "exponential"  # Exponentially increasing dropout rate
    RANDOM = "random"  # Random dropouts within a time window


class DropoutConfig(BaseModel):
    """Configuration for device dropout/failure simulation."""

    strategy: DropoutStrategy = DropoutStrategy.LINEAR
    count: int | None = Field(None, ge=1)  # Number of devices to drop (None = percentage-based)
    percentage: float | None = Field(None, ge=0, le=100)  # Percentage of devices to drop
    delay_ms: int = Field(1000, alias="delayMs", ge=0)  # Base delay between dropouts
    duration_ms: int = Field(60000, alias="durationMs", ge=0)  # Total duration for dropouts
    exponent_base: float = Field(1.5, alias="exponentBase", ge=1.0)  # For exponential strategy
    reconnect: bool = False  # Whether devices should reconnect after dropout
    reconnect_delay_ms: int = Field(0, alias="reconnectDelayMs", ge=0)  # Delay before reconnect


class DropoutRequest(BaseModel):
    """Request to simulate device dropouts in a group."""

    group_id: str = Field(alias="groupId")
    config: DropoutConfig


class DropoutResponse(BaseModel):
    """Response for dropout operation."""

    group_id: str = Field(alias="groupId")
    devices_affected: int = Field(alias="devicesAffected")
    dropout_strategy: str = Field(alias="dropoutStrategy")
    status: str
    estimated_duration_ms: int = Field(alias="estimatedDurationMs")

    model_config = {"populate_by_name": True}


class CreateDeviceGroupRequest(BaseModel):
    """Request to create a device group."""

    model_id: str = Field(alias="modelId")
    count: int = Field(ge=1, le=100000)
    group_id: str | None = Field(None, alias="groupId")
    id_pattern: str = Field("device-{index}", alias="idPattern")
    stagger_ms: int = Field(0, alias="staggerMs")  # Deprecated, use launch_config
    launch_config: LaunchConfig | None = Field(None, alias="launchConfig")


class DeviceGroupResponse(BaseModel):
    """Response for device group operations."""

    group_id: str = Field(serialization_alias="groupId")
    device_count: int = Field(serialization_alias="deviceCount")
    devices_created: int = Field(serialization_alias="devicesCreated")
    devices_started: int = Field(serialization_alias="devicesStarted")
    devices_stopped: int = Field(serialization_alias="devicesStopped")
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


# Proxy Device Models


class BindingConfig(BaseModel):
    """Configuration for binding a proxy device to an external source."""

    protocol: Protocol
    broker: str | None = None
    port: int | None = None
    topic: str | None = None
    qos: int = Field(1, ge=0, le=2)
    username: str | None = None
    password_ref: str | None = Field(None, alias="passwordRef")
    webhook_path: str | None = Field(None, alias="webhookPath")
    resource_uri: str | None = Field(None, alias="resourceUri")

    model_config = {"populate_by_name": True}


class BindingStatus(BaseModel):
    """Status of a proxy device binding."""

    bound: bool
    protocol: Protocol | None = None
    broker: str | None = None
    port: int | None = None
    topic: str | None = None
    webhook_url: str | None = Field(None, alias="webhookUrl")
    resource_uri: str | None = Field(None, alias="resourceUri")
    bound_at: datetime | None = Field(None, alias="boundAt")

    model_config = {"populate_by_name": True}


class BindRequest(BaseModel):
    """Request to bind a proxy device to an external source."""

    config: BindingConfig


class BindResponse(BaseModel):
    """Response for bind/unbind operations."""

    device_id: str = Field(serialization_alias="deviceId")
    status: str
    binding: BindingStatus | None = None
    webhook_url: str | None = Field(None, serialization_alias="webhookUrl")
