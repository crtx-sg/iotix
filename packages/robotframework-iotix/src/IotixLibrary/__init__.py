"""Robot Framework library for IoTix device simulation testing."""

import json
import time
from typing import Any

import httpx

__version__ = "0.1.0"


class IotixLibrary:
    """
    Robot Framework library for IoTix device simulation platform.

    This library provides keywords for:
    - Managing device models and instances
    - Creating and controlling device groups
    - Validating telemetry and metrics
    - Interacting with the device engine API

    Example usage:
    | Library | IotixLibrary | base_url=http://localhost:8080 |
    | ${model} | Register Device Model | ${model_json} |
    | ${device} | Create Device | model_id=${model}[id] |
    | Start Device | ${device}[id] |
    | ${metrics} | Get Device Metrics | ${device}[id] |
    | Should Be Greater Than | ${metrics}[messagesSent] | 0 |
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        """Initialize the library.

        Args:
            base_url: Base URL of the device engine API
            timeout: Default timeout for API requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    # Model Keywords

    def register_device_model(self, model: dict | str) -> dict[str, Any]:
        """Register a new device model.

        Args:
            model: Device model configuration as dict or JSON string

        Returns:
            Registered model data

        Example:
        | ${model} | Register Device Model | {"id": "test-sensor", "name": "Test", "type": "sensor", "protocol": "mqtt"} |
        """
        if isinstance(model, str):
            model = json.loads(model)

        response = self._client.post("/api/v1/models", json=model)
        response.raise_for_status()
        return response.json()

    def get_device_model(self, model_id: str) -> dict[str, Any]:
        """Get a device model by ID.

        Args:
            model_id: Model identifier

        Returns:
            Model data
        """
        response = self._client.get(f"/api/v1/models/{model_id}")
        response.raise_for_status()
        return response.json()

    def list_device_models(self) -> list[dict[str, Any]]:
        """List all registered device models.

        Returns:
            List of model data
        """
        response = self._client.get("/api/v1/models")
        response.raise_for_status()
        return response.json()

    # Device Keywords

    def create_device(
        self,
        model_id: str,
        device_id: str | None = None,
        group_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new device instance.

        Args:
            model_id: Model identifier to use
            device_id: Optional device ID (auto-generated if not provided)
            group_id: Optional group ID

        Returns:
            Created device data
        """
        payload = {"modelId": model_id}
        if device_id:
            payload["deviceId"] = device_id
        if group_id:
            payload["groupId"] = group_id

        response = self._client.post("/api/v1/devices", json=payload)
        response.raise_for_status()
        return response.json()

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Get device details.

        Args:
            device_id: Device identifier

        Returns:
            Device data
        """
        response = self._client.get(f"/api/v1/devices/{device_id}")
        response.raise_for_status()
        return response.json()

    def start_device(self, device_id: str) -> dict[str, Any]:
        """Start a device.

        Args:
            device_id: Device identifier

        Returns:
            Updated device data
        """
        response = self._client.post(f"/api/v1/devices/{device_id}/start")
        response.raise_for_status()
        return response.json()

    def stop_device(self, device_id: str) -> dict[str, Any]:
        """Stop a device.

        Args:
            device_id: Device identifier

        Returns:
            Updated device data
        """
        response = self._client.post(f"/api/v1/devices/{device_id}/stop")
        response.raise_for_status()
        return response.json()

    def delete_device(self, device_id: str) -> None:
        """Delete a device.

        Args:
            device_id: Device identifier
        """
        response = self._client.delete(f"/api/v1/devices/{device_id}")
        response.raise_for_status()

    def get_device_metrics(self, device_id: str) -> dict[str, Any]:
        """Get device metrics.

        Args:
            device_id: Device identifier

        Returns:
            Device metrics
        """
        response = self._client.get(f"/api/v1/devices/{device_id}/metrics")
        response.raise_for_status()
        return response.json()

    def device_should_be_running(self, device_id: str) -> None:
        """Assert that a device is in running state.

        Args:
            device_id: Device identifier
        """
        device = self.get_device(device_id)
        if device["status"] != "running":
            raise AssertionError(
                f"Device {device_id} is not running. Status: {device['status']}"
            )

    def device_should_be_connected(self, device_id: str) -> None:
        """Assert that a device is connected.

        Args:
            device_id: Device identifier
        """
        device = self.get_device(device_id)
        if device["connectionState"] != "connected":
            raise AssertionError(
                f"Device {device_id} is not connected. State: {device['connectionState']}"
            )

    # Group Keywords

    def create_device_group(
        self,
        model_id: str,
        count: int,
        group_id: str | None = None,
        id_pattern: str = "device-{index}",
    ) -> dict[str, Any]:
        """Create a group of devices.

        Args:
            model_id: Model identifier
            count: Number of devices to create
            group_id: Optional group ID
            id_pattern: Pattern for device IDs

        Returns:
            Group creation result
        """
        payload = {
            "modelId": model_id,
            "count": count,
            "idPattern": id_pattern,
        }
        if group_id:
            payload["groupId"] = group_id

        response = self._client.post("/api/v1/groups", json=payload)
        response.raise_for_status()
        return response.json()

    def start_device_group(
        self, group_id: str, stagger_ms: int = 0
    ) -> dict[str, Any]:
        """Start all devices in a group.

        Args:
            group_id: Group identifier
            stagger_ms: Delay between starting devices

        Returns:
            Group operation result
        """
        response = self._client.post(
            f"/api/v1/groups/{group_id}/start",
            params={"staggerMs": stagger_ms},
        )
        response.raise_for_status()
        return response.json()

    def stop_device_group(self, group_id: str) -> dict[str, Any]:
        """Stop all devices in a group.

        Args:
            group_id: Group identifier

        Returns:
            Group operation result
        """
        response = self._client.post(f"/api/v1/groups/{group_id}/stop")
        response.raise_for_status()
        return response.json()

    def delete_device_group(self, group_id: str) -> None:
        """Delete a device group and all its devices.

        Args:
            group_id: Group identifier
        """
        response = self._client.delete(f"/api/v1/groups/{group_id}")
        response.raise_for_status()

    # Utility Keywords

    def wait_for_telemetry(
        self,
        device_id: str,
        min_messages: int = 1,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Wait for device to send telemetry.

        Args:
            device_id: Device identifier
            min_messages: Minimum number of messages to wait for
            timeout: Maximum wait time in seconds

        Returns:
            Device metrics after waiting
        """
        start = time.time()
        while time.time() - start < timeout:
            metrics = self.get_device_metrics(device_id)
            if metrics["messagesSent"] >= min_messages:
                return metrics
            time.sleep(1)

        raise TimeoutError(
            f"Timeout waiting for telemetry from device {device_id}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get device engine statistics.

        Returns:
            Engine statistics
        """
        response = self._client.get("/api/v1/stats")
        response.raise_for_status()
        return response.json()
