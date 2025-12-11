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
from .models import (
    ConnectionConfig,
    DeviceModelConfig,
    DeviceStatus,
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

    async def start_group(self, group_id: str, stagger_ms: int = 0) -> int:
        """Start all devices in a group."""
        if group_id not in self._groups:
            raise ValueError(f"Group not found: {group_id}")

        started = 0
        device_ids = list(self._groups[group_id])

        for device_id in device_ids:
            device = self._devices.get(device_id)
            if device and device.status != DeviceStatus.RUNNING:
                try:
                    await device.start()
                    started += 1
                except Exception as e:
                    logger.error(f"Failed to start device {device_id}: {e}")

                if stagger_ms > 0:
                    await asyncio.sleep(stagger_ms / 1000.0)

        return started

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
