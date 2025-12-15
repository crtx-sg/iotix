"""Device Engine API - FastAPI application."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .manager import device_manager
from .metrics import init_metrics, close_metrics
from .models import (
    BindingConfig,
    BindRequest,
    BindResponse,
    BindingStatus,
    ConnectionConfig,
    CreateDeviceGroupRequest,
    CreateDeviceRequest,
    DeviceGroupResponse,
    DeviceInstance,
    DeviceMetrics,
    DeviceModelConfig,
    DeviceStatus,
    DropoutConfig,
    DropoutResponse,
    HealthResponse,
    LaunchConfig,
    PaginatedResponse,
)
from .adapters.http_proxy import get_webhook_handler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Track startup time
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Device Engine...")
    await init_metrics()
    await device_manager.initialize()
    logger.info("Device Engine started")

    yield

    # Shutdown
    logger.info("Shutting down Device Engine...")
    await device_manager.shutdown()
    await close_metrics()
    logger.info("Device Engine shutdown complete")


app = FastAPI(
    title="IoTix Device Engine",
    description="Virtual IoT device simulation engine",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoints


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check service health."""
    stats = device_manager.get_stats()
    return HealthResponse(
        status="healthy",
        version=__version__,
        uptime_seconds=time.time() - start_time,
        device_count=stats["total_devices"],
        running_device_count=stats["running_devices"],
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """Check if service is ready to accept requests."""
    return {"status": "ready"}


# Model endpoints


@app.get("/api/v1/models", tags=["Models"])
async def list_models() -> list[dict[str, Any]]:
    """List all registered device models."""
    models = device_manager.list_models()
    return [m.model_dump(by_alias=True) for m in models]


@app.get("/api/v1/models/{model_id}", tags=["Models"])
async def get_model(model_id: str) -> dict[str, Any]:
    """Get a device model by ID."""
    model = device_manager.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    return model.model_dump(by_alias=True)


@app.post("/api/v1/models", status_code=201, tags=["Models"])
async def register_model(model: DeviceModelConfig) -> dict[str, Any]:
    """Register a new device model."""
    existing = device_manager.get_model(model.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Model already exists: {model.id}")
    device_manager.register_model(model)
    return model.model_dump(by_alias=True)


# Device endpoints


@app.get("/api/v1/devices", response_model=PaginatedResponse, tags=["Devices"])
async def list_devices(
    status: DeviceStatus | None = None,
    group_id: str | None = Query(None, alias="groupId"),
    model_id: str | None = Query(None, alias="modelId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000, alias="pageSize"),
) -> PaginatedResponse:
    """List devices with optional filtering."""
    devices, total = device_manager.list_devices(
        status=status,
        group_id=group_id,
        model_id=model_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[d.to_dict() for d in devices],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@app.post("/api/v1/devices", status_code=201, tags=["Devices"])
async def create_device(request: CreateDeviceRequest) -> dict[str, Any]:
    """Create a new device instance."""
    try:
        device = await device_manager.create_device(
            model_id=request.model_id,
            device_id=request.device_id,
            group_id=request.group_id,
            connection_override=request.override_connection,
        )
        return device.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/v1/devices/{device_id}", tags=["Devices"])
async def get_device(device_id: str) -> dict[str, Any]:
    """Get device details by ID."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return device.to_dict()


@app.delete("/api/v1/devices/{device_id}", status_code=204, tags=["Devices"])
async def delete_device(device_id: str) -> None:
    """Delete a device."""
    try:
        await device_manager.delete_device(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/devices/{device_id}/start", tags=["Devices"])
async def start_device(device_id: str) -> dict[str, Any]:
    """Start a device."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    try:
        await device_manager.start_device(device_id)
        return device.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/devices/{device_id}/stop", tags=["Devices"])
async def stop_device(device_id: str) -> dict[str, Any]:
    """Stop a device."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    await device_manager.stop_device(device_id)
    return device.to_dict()


@app.get("/api/v1/devices/{device_id}/metrics", response_model=DeviceMetrics, tags=["Devices"])
async def get_device_metrics(device_id: str) -> DeviceMetrics:
    """Get device metrics."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    metrics = device.get_metrics()
    return DeviceMetrics(**metrics)


# Group endpoints


@app.post("/api/v1/groups", status_code=201, tags=["Groups"])
async def create_device_group(request: CreateDeviceGroupRequest) -> DeviceGroupResponse:
    """Create a group of devices."""
    try:
        group_id, devices = await device_manager.create_device_group(
            model_id=request.model_id,
            count=request.count,
            group_id=request.group_id,
            id_pattern=request.id_pattern,
            stagger_ms=request.stagger_ms,
        )
        return DeviceGroupResponse(
            group_id=group_id,
            device_count=len(devices),
            devices_created=len(devices),
            devices_started=0,
            devices_stopped=0,
            status="created",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/groups/{group_id}/start", tags=["Groups"])
async def start_group(
    group_id: str,
    stagger_ms: int = Query(0, alias="staggerMs"),
    launch_config: LaunchConfig | None = None,
) -> DeviceGroupResponse:
    """Start all devices in a group.

    Supports multiple launch strategies via launch_config:
    - immediate: Start all devices at once (default)
    - linear: Fixed delay between each device
    - batch: Start devices in batches with delay between batches
    - exponential: Exponentially increasing delay between devices

    For backward compatibility, staggerMs query param is still supported
    and maps to the 'linear' strategy.
    """
    try:
        started = await device_manager.start_group(group_id, stagger_ms, launch_config)
        devices, _ = device_manager.list_devices(group_id=group_id)
        return DeviceGroupResponse(
            group_id=group_id,
            device_count=len(devices),
            devices_created=len(devices),
            devices_started=started,
            devices_stopped=0,
            status="started",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/groups/{group_id}/stop", tags=["Groups"])
async def stop_group(group_id: str) -> DeviceGroupResponse:
    """Stop all devices in a group."""
    try:
        stopped = await device_manager.stop_group(group_id)
        devices, _ = device_manager.list_devices(group_id=group_id)
        return DeviceGroupResponse(
            group_id=group_id,
            device_count=len(devices),
            devices_created=len(devices),
            devices_started=0,
            devices_stopped=stopped,
            status="stopped",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/v1/groups/{group_id}", status_code=204, tags=["Groups"])
async def delete_group(group_id: str) -> None:
    """Delete a device group and all its devices."""
    try:
        await device_manager.delete_group(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/groups/{group_id}/dropout", tags=["Groups"])
async def simulate_group_dropout(
    group_id: str,
    config: DropoutConfig,
) -> DropoutResponse:
    """Simulate device dropouts/failures in a group.

    Supports multiple dropout strategies:
    - immediate: All specified devices drop at once
    - linear: Fixed delay between each dropout
    - exponential: Exponentially increasing dropout rate
    - random: Random dropouts within a time window

    You can specify either 'count' (absolute number) or 'percentage'
    of devices to drop. If both are provided, 'count' takes precedence.

    Set 'reconnect: true' to have devices automatically reconnect
    after the specified reconnect_delay_ms.
    """
    try:
        devices_affected, estimated_duration = await device_manager.simulate_dropouts(
            group_id, config
        )
        return DropoutResponse(
            group_id=group_id,
            devices_affected=devices_affected,
            dropout_strategy=config.strategy.value,
            status="dropout_initiated",
            estimated_duration_ms=estimated_duration,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Stats endpoint


@app.get("/api/v1/stats", tags=["Stats"])
async def get_stats() -> dict[str, Any]:
    """Get device engine statistics."""
    return device_manager.get_stats()


# Proxy device binding endpoints


@app.post("/api/v1/devices/{device_id}/bind", tags=["Devices"])
async def bind_device(device_id: str, request: BindRequest) -> BindResponse:
    """Bind a proxy device to an external telemetry source.

    Supported protocols:
    - mqtt: Subscribe to an external MQTT topic
    - http: Receive telemetry via HTTP webhook POST

    For MQTT, provide: broker, port, topic, and optionally username/passwordRef
    For HTTP, webhook URL will be returned for external devices to POST to
    """
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    try:
        webhook_url = await device_manager.bind_device(device_id, request.config)

        # Get fresh binding status
        from .proxy_device import ProxyDevice

        if isinstance(device, ProxyDevice):
            binding_status = device.get_binding_status()
        else:
            binding_status = None

        return BindResponse(
            device_id=device_id,
            status="bound",
            binding=binding_status,
            webhook_url=webhook_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/devices/{device_id}/unbind", tags=["Devices"])
async def unbind_device(device_id: str) -> BindResponse:
    """Unbind a proxy device from its external telemetry source."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    try:
        await device_manager.unbind_device(device_id)
        return BindResponse(
            device_id=device_id,
            status="unbound",
            binding=None,
            webhook_url=None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/devices/{device_id}/binding", tags=["Devices"])
async def get_device_binding(device_id: str) -> BindingStatus:
    """Get binding status for a proxy device."""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    from .proxy_device import ProxyDevice

    if not isinstance(device, ProxyDevice):
        raise HTTPException(
            status_code=400, detail=f"Device {device_id} is not a proxy device"
        )

    return device.get_binding_status()


# Webhook endpoint for receiving external telemetry


@app.post("/api/v1/webhooks/{device_id}", tags=["Webhooks"])
async def receive_webhook(device_id: str, payload: dict[str, Any]) -> dict[str, str]:
    """Receive telemetry from external device via webhook.

    This endpoint is called by external physical devices to send telemetry data.
    The device must be bound via HTTP protocol for this endpoint to accept data.
    """
    handler = get_webhook_handler(device_id)
    if not handler:
        raise HTTPException(
            status_code=404,
            detail=f"No webhook handler registered for device: {device_id}",
        )

    try:
        await handler(payload)
        return {"status": "accepted", "deviceId": device_id}
    except Exception as e:
        logger.error(f"Error processing webhook for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
