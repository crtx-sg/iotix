"""Device manager for handling device lifecycle and model registry."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import settings
from .device import VirtualDevice
import random

from .models import (
    ConnectionConfig,
    DeviceModelConfig,
    DeviceStatus,
    DropoutConfig,
    DropoutStrategy,
    LaunchConfig,
    LaunchStrategy,
)

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages device models and device instances."""

    def __init__(self):
        self._models: dict[str, DeviceModelConfig] = {}
        self._devices: dict[str, VirtualDevice] = {}
        self._groups: dict[str, set[str]] = {}  # group_id -> device_ids
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the device manager."""
        await self._load_models_from_directory(settings.device_model_path)
        logger.info(f"Device manager initialized with {len(self._models)} models")

    async def _load_models_from_directory(self, path: str) -> None:
        """Load device models from a directory."""
        model_path = Path(path)
        if not model_path.exists():
            logger.warning(f"Device model path does not exist: {path}")
            return

        for file_path in model_path.glob("**/*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                model = DeviceModelConfig(**data)
                self._models[model.id] = model
                logger.info(f"Loaded device model: {model.id}")
            except Exception as e:
                logger.error(f"Failed to load device model from {file_path}: {e}")

    def register_model(self, model: DeviceModelConfig) -> None:
        """Register a device model."""
        self._models[model.id] = model
        logger.info(f"Registered device model: {model.id}")

    def get_model(self, model_id: str) -> DeviceModelConfig | None:
        """Get a device model by ID."""
        return self._models.get(model_id)

    def list_models(self) -> list[DeviceModelConfig]:
        """List all registered device models."""
        return list(self._models.values())

    async def create_device(
        self,
        model_id: str,
        device_id: str | None = None,
        group_id: str | None = None,
        connection_override: ConnectionConfig | None = None,
    ) -> VirtualDevice:
        """Create a new device instance."""
        model = self._models.get(model_id)
        if not model:
            raise ValueError(f"Unknown device model: {model_id}")

        if len(self._devices) >= settings.max_devices_per_instance:
            raise RuntimeError(
                f"Maximum device count ({settings.max_devices_per_instance}) reached"
            )

        device_id = device_id or f"{model_id}-{uuid4().hex[:8]}"

        async with self._lock:
            if device_id in self._devices:
                raise ValueError(f"Device already exists: {device_id}")

            device = VirtualDevice(
                device_id=device_id,
                model=model,
                connection_override=connection_override,
                group_id=group_id,
            )
            self._devices[device_id] = device

            if group_id:
                if group_id not in self._groups:
                    self._groups[group_id] = set()
                self._groups[group_id].add(device_id)

        logger.info(f"Created device: {device_id}")
        return device

    async def create_device_group(
        self,
        model_id: str,
        count: int,
        group_id: str | None = None,
        id_pattern: str = "device-{index}",
        stagger_ms: int = 0,
    ) -> tuple[str, list[VirtualDevice]]:
        """Create a group of devices."""
        group_id = group_id or f"group-{uuid4().hex[:8]}"
        devices = []

        for i in range(count):
            device_id = id_pattern.format(index=i, groupId=group_id)
            device = await self.create_device(
                model_id=model_id,
                device_id=device_id,
                group_id=group_id,
            )
            devices.append(device)

            if stagger_ms > 0 and i < count - 1:
                await asyncio.sleep(stagger_ms / 1000.0)

        logger.info(f"Created device group {group_id} with {count} devices")
        return group_id, devices

    def get_device(self, device_id: str) -> VirtualDevice | None:
        """Get a device by ID."""
        return self._devices.get(device_id)

    def list_devices(
        self,
        status: DeviceStatus | None = None,
        group_id: str | None = None,
        model_id: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[VirtualDevice], int]:
        """List devices with optional filtering and pagination."""
        devices = list(self._devices.values())

        # Apply filters
        if status:
            devices = [d for d in devices if d.status == status]
        if group_id:
            devices = [d for d in devices if d.group_id == group_id]
        if model_id:
            devices = [d for d in devices if d.model.id == model_id]

        total = len(devices)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        devices = devices[start:end]

        return devices, total

    async def start_device(self, device_id: str) -> None:
        """Start a device."""
        device = self._devices.get(device_id)
        if not device:
            raise ValueError(f"Device not found: {device_id}")
        await device.start()

    async def stop_device(self, device_id: str) -> None:
        """Stop a device."""
        device = self._devices.get(device_id)
        if not device:
            raise ValueError(f"Device not found: {device_id}")
        await device.stop()

    async def delete_device(self, device_id: str) -> None:
        """Delete a device."""
        async with self._lock:
            device = self._devices.get(device_id)
            if not device:
                raise ValueError(f"Device not found: {device_id}")

            if device.status == DeviceStatus.RUNNING:
                await device.stop()

            del self._devices[device_id]

            # Remove from group
            if device.group_id and device.group_id in self._groups:
                self._groups[device.group_id].discard(device_id)
                if not self._groups[device.group_id]:
                    del self._groups[device.group_id]

        logger.info(f"Deleted device: {device_id}")

    async def start_group(
        self,
        group_id: str,
        stagger_ms: int = 0,
        launch_config: LaunchConfig | None = None,
    ) -> int:
        """Start all devices in a group with configurable launch strategy.

        Launch strategies:
        - IMMEDIATE: Start all devices at once (default)
        - LINEAR: Fixed delay between each device
        - BATCH: Start devices in batches with delay between batches
        - EXPONENTIAL: Exponentially increasing delay between devices
        """
        if group_id not in self._groups:
            raise ValueError(f"Group not found: {group_id}")

        started = 0
        device_ids = list(self._groups[group_id])
        total_devices = len(device_ids)

        # Use launch_config if provided, otherwise fall back to stagger_ms
        if launch_config is None:
            if stagger_ms > 0:
                launch_config = LaunchConfig(
                    strategy=LaunchStrategy.LINEAR, delay_ms=stagger_ms
                )
            else:
                launch_config = LaunchConfig(strategy=LaunchStrategy.IMMEDIATE)

        logger.info(
            f"Starting group {group_id} with {total_devices} devices "
            f"using {launch_config.strategy.value} strategy"
        )

        if launch_config.strategy == LaunchStrategy.IMMEDIATE:
            # Start all devices concurrently
            tasks = []
            for device_id in device_ids:
                device = self._devices.get(device_id)
                if device and device.status != DeviceStatus.RUNNING:
                    tasks.append(self._start_device_safe(device))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            started = sum(1 for r in results if r is True)

        elif launch_config.strategy == LaunchStrategy.LINEAR:
            # Fixed delay between each device
            for device_id in device_ids:
                device = self._devices.get(device_id)
                if device and device.status != DeviceStatus.RUNNING:
                    if await self._start_device_safe(device):
                        started += 1
                    if launch_config.delay_ms > 0:
                        await asyncio.sleep(launch_config.delay_ms / 1000.0)

        elif launch_config.strategy == LaunchStrategy.BATCH:
            # Start in batches
            batch_size = launch_config.batch_size
            for i in range(0, total_devices, batch_size):
                batch = device_ids[i : i + batch_size]
                tasks = []
                for device_id in batch:
                    device = self._devices.get(device_id)
                    if device and device.status != DeviceStatus.RUNNING:
                        tasks.append(self._start_device_safe(device))
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    started += sum(1 for r in results if r is True)
                    logger.info(
                        f"Started batch {i // batch_size + 1}, "
                        f"total started: {started}/{total_devices}"
                    )
                if launch_config.delay_ms > 0 and i + batch_size < total_devices:
                    await asyncio.sleep(launch_config.delay_ms / 1000.0)

        elif launch_config.strategy == LaunchStrategy.EXPONENTIAL:
            # Exponentially increasing delay
            base = launch_config.exponent_base
            for idx, device_id in enumerate(device_ids):
                device = self._devices.get(device_id)
                if device and device.status != DeviceStatus.RUNNING:
                    if await self._start_device_safe(device):
                        started += 1
                    # Calculate exponential delay: delay_ms * (base ^ idx)
                    delay = min(
                        launch_config.delay_ms * (base**idx),
                        launch_config.max_delay_ms,
                    )
                    if delay > 0 and idx < total_devices - 1:
                        await asyncio.sleep(delay / 1000.0)

        logger.info(f"Started {started}/{total_devices} devices in group {group_id}")
        return started

    async def _start_device_safe(self, device: VirtualDevice) -> bool:
        """Safely start a device, catching exceptions."""
        try:
            await device.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start device {device.device_id}: {e}")
            return False

    async def stop_group(self, group_id: str) -> int:
        """Stop all devices in a group."""
        if group_id not in self._groups:
            raise ValueError(f"Group not found: {group_id}")

        stopped = 0
        device_ids = list(self._groups[group_id])

        for device_id in device_ids:
            device = self._devices.get(device_id)
            if device and device.status == DeviceStatus.RUNNING:
                try:
                    await device.stop()
                    stopped += 1
                except Exception as e:
                    logger.error(f"Failed to stop device {device_id}: {e}")

        return stopped

    async def delete_group(self, group_id: str) -> int:
        """Delete all devices in a group."""
        if group_id not in self._groups:
            raise ValueError(f"Group not found: {group_id}")

        deleted = 0
        device_ids = list(self._groups[group_id])

        for device_id in device_ids:
            try:
                await self.delete_device(device_id)
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete device {device_id}: {e}")

        return deleted

    def get_stats(self) -> dict[str, Any]:
        """Get device manager statistics."""
        running = sum(1 for d in self._devices.values() if d.status == DeviceStatus.RUNNING)
        return {
            "total_devices": len(self._devices),
            "running_devices": running,
            "total_groups": len(self._groups),
            "total_models": len(self._models),
        }

    async def simulate_dropouts(
        self,
        group_id: str,
        config: DropoutConfig,
    ) -> tuple[int, int]:
        """Simulate device dropouts/failures in a group.

        Dropout strategies:
        - IMMEDIATE: Drop all specified devices at once
        - LINEAR: Fixed delay between each dropout
        - EXPONENTIAL: Exponentially increasing dropout rate
        - RANDOM: Random dropouts distributed across a time window

        Returns:
            Tuple of (devices_dropped, estimated_duration_ms)
        """
        if group_id not in self._groups:
            raise ValueError(f"Group not found: {group_id}")

        device_ids = list(self._groups[group_id])
        running_devices = [
            did for did in device_ids
            if self._devices.get(did) and self._devices[did].status == DeviceStatus.RUNNING
        ]

        if not running_devices:
            return 0, 0

        # Determine how many devices to drop
        if config.count is not None:
            dropout_count = min(config.count, len(running_devices))
        elif config.percentage is not None:
            dropout_count = int(len(running_devices) * config.percentage / 100)
        else:
            dropout_count = len(running_devices)

        # Select devices to drop (randomly)
        devices_to_drop = random.sample(running_devices, dropout_count)

        logger.info(
            f"Simulating {dropout_count} dropouts in group {group_id} "
            f"using {config.strategy.value} strategy"
        )

        dropped = 0
        estimated_duration = 0

        if config.strategy == DropoutStrategy.IMMEDIATE:
            # Drop all devices at once
            tasks = [self._stop_device_safe(self._devices[did]) for did in devices_to_drop]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            dropped = sum(1 for r in results if r is True)
            estimated_duration = 0

        elif config.strategy == DropoutStrategy.LINEAR:
            # Fixed delay between each dropout
            for idx, device_id in enumerate(devices_to_drop):
                device = self._devices.get(device_id)
                if device:
                    if await self._stop_device_safe(device):
                        dropped += 1
                    if config.delay_ms > 0 and idx < len(devices_to_drop) - 1:
                        await asyncio.sleep(config.delay_ms / 1000.0)
            estimated_duration = config.delay_ms * (dropout_count - 1)

        elif config.strategy == DropoutStrategy.EXPONENTIAL:
            # Exponentially increasing dropout rate (decreasing delay)
            base = config.exponent_base
            for idx, device_id in enumerate(devices_to_drop):
                device = self._devices.get(device_id)
                if device:
                    if await self._stop_device_safe(device):
                        dropped += 1
                    # Delay decreases exponentially (faster dropouts over time)
                    delay = config.delay_ms / (base ** idx)
                    delay = max(delay, 1)  # Minimum 1ms delay
                    estimated_duration += int(delay)
                    if idx < len(devices_to_drop) - 1:
                        await asyncio.sleep(delay / 1000.0)

        elif config.strategy == DropoutStrategy.RANDOM:
            # Random dropouts distributed across duration window
            if config.duration_ms > 0:
                # Generate random times within the duration
                dropout_times = sorted([
                    random.uniform(0, config.duration_ms / 1000.0)
                    for _ in range(dropout_count)
                ])
                estimated_duration = config.duration_ms

                last_time = 0
                for idx, dropout_time in enumerate(dropout_times):
                    # Wait until the scheduled dropout time
                    wait_time = dropout_time - last_time
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    last_time = dropout_time

                    device = self._devices.get(devices_to_drop[idx])
                    if device:
                        if await self._stop_device_safe(device):
                            dropped += 1
            else:
                # No duration specified, drop immediately with small random delays
                for device_id in devices_to_drop:
                    device = self._devices.get(device_id)
                    if device:
                        if await self._stop_device_safe(device):
                            dropped += 1
                        await asyncio.sleep(random.uniform(0, 0.1))

        logger.info(f"Dropped {dropped}/{dropout_count} devices in group {group_id}")

        # Handle reconnection if configured
        if config.reconnect and dropped > 0:
            asyncio.create_task(
                self._reconnect_devices(devices_to_drop[:dropped], config.reconnect_delay_ms)
            )

        return dropped, estimated_duration

    async def _stop_device_safe(self, device: VirtualDevice) -> bool:
        """Safely stop a device, catching exceptions."""
        try:
            await device.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop device {device.device_id}: {e}")
            return False

    async def _reconnect_devices(self, device_ids: list[str], delay_ms: int) -> None:
        """Reconnect devices after a delay."""
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)

        logger.info(f"Reconnecting {len(device_ids)} devices...")
        for device_id in device_ids:
            device = self._devices.get(device_id)
            if device and device.status != DeviceStatus.RUNNING:
                try:
                    await device.start()
                except Exception as e:
                    logger.error(f"Failed to reconnect device {device_id}: {e}")

    async def shutdown(self) -> None:
        """Shutdown the device manager."""
        logger.info("Shutting down device manager...")

        # Stop all running devices
        for device in self._devices.values():
            if device.status == DeviceStatus.RUNNING:
                try:
                    await device.stop()
                except Exception as e:
                    logger.error(f"Error stopping device {device.device_id}: {e}")

        self._devices.clear()
        self._groups.clear()
        logger.info("Device manager shutdown complete")


# Singleton instance
device_manager = DeviceManager()
