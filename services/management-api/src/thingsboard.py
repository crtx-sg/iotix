"""ThingsBoard integration client for IoTix."""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ThingsBoardClient:
    """Client for ThingsBoard REST API integration.

    Provides methods to:
    - Sync devices with ThingsBoard
    - Forward telemetry data
    - Handle commands from ThingsBoard
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30,
    ):
        """Initialize ThingsBoard client.

        Args:
            base_url: ThingsBoard server URL
            username: ThingsBoard username
            password: ThingsBoard password
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Connect and authenticate with ThingsBoard."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        await self._authenticate()

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _authenticate(self) -> None:
        """Authenticate with ThingsBoard and get JWT token."""
        if not self._client:
            raise RuntimeError("Client not connected")

        response = await self._client.post(
            "/api/auth/login",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["token"]
        self._refresh_token = data.get("refreshToken")
        logger.info("Authenticated with ThingsBoard")

    async def _refresh_auth(self) -> None:
        """Refresh the authentication token."""
        if not self._client or not self._refresh_token:
            await self._authenticate()
            return

        response = await self._client.post(
            "/api/auth/token",
            json={"refreshToken": self._refresh_token},
        )
        if response.status_code == 200:
            data = response.json()
            self._token = data["token"]
            self._refresh_token = data.get("refreshToken", self._refresh_token)
        else:
            await self._authenticate()

    def _headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {"X-Authorization": f"Bearer {self._token}"}

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an authenticated request to ThingsBoard.

        Args:
            method: HTTP method
            path: API path
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        if not self._client:
            raise RuntimeError("Client not connected")

        kwargs.setdefault("headers", {}).update(self._headers())
        response = await self._client.request(method, path, **kwargs)

        # Refresh token if expired
        if response.status_code == 401:
            await self._refresh_auth()
            kwargs["headers"].update(self._headers())
            response = await self._client.request(method, path, **kwargs)

        return response

    # Device Management

    async def create_device(
        self,
        name: str,
        device_type: str,
        label: str | None = None,
        additional_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a device in ThingsBoard.

        Args:
            name: Device name
            device_type: Device type/profile
            label: Optional device label
            additional_info: Optional additional info

        Returns:
            Created device data
        """
        device_data = {
            "name": name,
            "type": device_type,
        }
        if label:
            device_data["label"] = label
        if additional_info:
            device_data["additionalInfo"] = additional_info

        response = await self._request("POST", "/api/device", json=device_data)
        response.raise_for_status()
        return response.json()

    async def get_device(self, device_id: str) -> dict[str, Any]:
        """Get device by ID.

        Args:
            device_id: ThingsBoard device ID

        Returns:
            Device data
        """
        response = await self._request("GET", f"/api/device/{device_id}")
        response.raise_for_status()
        return response.json()

    async def get_device_by_name(self, name: str) -> dict[str, Any] | None:
        """Get device by name.

        Args:
            name: Device name

        Returns:
            Device data or None if not found
        """
        response = await self._request(
            "GET",
            "/api/tenant/devices",
            params={"deviceName": name},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def delete_device(self, device_id: str) -> None:
        """Delete a device.

        Args:
            device_id: ThingsBoard device ID
        """
        response = await self._request("DELETE", f"/api/device/{device_id}")
        response.raise_for_status()

    async def get_device_credentials(self, device_id: str) -> dict[str, Any]:
        """Get device credentials.

        Args:
            device_id: ThingsBoard device ID

        Returns:
            Device credentials
        """
        response = await self._request(
            "GET", f"/api/device/{device_id}/credentials"
        )
        response.raise_for_status()
        return response.json()

    # Telemetry

    async def send_telemetry(
        self,
        device_id: str,
        telemetry: dict[str, Any],
        timestamp: int | None = None,
    ) -> None:
        """Send telemetry data for a device.

        Args:
            device_id: ThingsBoard device ID
            telemetry: Telemetry key-value pairs
            timestamp: Optional timestamp in milliseconds
        """
        data = telemetry
        if timestamp:
            data = {"ts": timestamp, "values": telemetry}

        response = await self._request(
            "POST",
            f"/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY",
            json=data,
        )
        response.raise_for_status()

    async def get_latest_telemetry(
        self,
        device_id: str,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get latest telemetry values for a device.

        Args:
            device_id: ThingsBoard device ID
            keys: Optional list of telemetry keys to fetch

        Returns:
            Telemetry data
        """
        params = {}
        if keys:
            params["keys"] = ",".join(keys)

        response = await self._request(
            "GET",
            f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # Attributes

    async def set_attributes(
        self,
        device_id: str,
        attributes: dict[str, Any],
        scope: str = "SERVER_SCOPE",
    ) -> None:
        """Set device attributes.

        Args:
            device_id: ThingsBoard device ID
            attributes: Attribute key-value pairs
            scope: Attribute scope (SERVER_SCOPE, SHARED_SCOPE, CLIENT_SCOPE)
        """
        response = await self._request(
            "POST",
            f"/api/plugins/telemetry/DEVICE/{device_id}/attributes/{scope}",
            json=attributes,
        )
        response.raise_for_status()

    async def get_attributes(
        self,
        device_id: str,
        keys: list[str] | None = None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """Get device attributes.

        Args:
            device_id: ThingsBoard device ID
            keys: Optional list of attribute keys
            scope: Optional attribute scope

        Returns:
            Attribute data
        """
        params = {}
        if keys:
            params["keys"] = ",".join(keys)

        path = f"/api/plugins/telemetry/DEVICE/{device_id}/values/attributes"
        if scope:
            path += f"/{scope}"

        response = await self._request("GET", path, params=params)
        response.raise_for_status()
        return response.json()

    # RPC Commands

    async def send_rpc(
        self,
        device_id: str,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: int = 10000,
    ) -> dict[str, Any]:
        """Send RPC command to device.

        Args:
            device_id: ThingsBoard device ID
            method: RPC method name
            params: RPC parameters
            timeout: Timeout in milliseconds

        Returns:
            RPC response
        """
        response = await self._request(
            "POST",
            f"/api/rpc/twoway/{device_id}",
            json={
                "method": method,
                "params": params or {},
                "timeout": timeout,
            },
        )
        response.raise_for_status()
        return response.json()

    # Device Profiles

    async def list_device_profiles(self) -> list[dict[str, Any]]:
        """List all device profiles.

        Returns:
            List of device profiles
        """
        response = await self._request(
            "GET",
            "/api/deviceProfiles",
            params={"pageSize": 100, "page": 0},
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def create_device_profile(
        self,
        name: str,
        profile_type: str = "DEFAULT",
        transport_type: str = "DEFAULT",
        provision_type: str = "DISABLED",
    ) -> dict[str, Any]:
        """Create a device profile.

        Args:
            name: Profile name
            profile_type: Profile type
            transport_type: Transport type (DEFAULT, MQTT, COAP, HTTP, etc.)
            provision_type: Provisioning type

        Returns:
            Created profile data
        """
        response = await self._request(
            "POST",
            "/api/deviceProfile",
            json={
                "name": name,
                "type": profile_type,
                "transportType": transport_type,
                "provisionType": provision_type,
            },
        )
        response.raise_for_status()
        return response.json()


class DeviceSyncService:
    """Service to sync IoTix devices with ThingsBoard."""

    def __init__(self, tb_client: ThingsBoardClient, device_engine_url: str):
        """Initialize sync service.

        Args:
            tb_client: ThingsBoard client
            device_engine_url: IoTix device engine URL
        """
        self.tb_client = tb_client
        self.device_engine_url = device_engine_url
        self._http_client: httpx.AsyncClient | None = None
        self._device_mapping: dict[str, str] = {}  # iotix_id -> tb_id

    async def start(self) -> None:
        """Start the sync service."""
        self._http_client = httpx.AsyncClient(base_url=self.device_engine_url)
        await self.tb_client.connect()
        logger.info("Device sync service started")

    async def stop(self) -> None:
        """Stop the sync service."""
        if self._http_client:
            await self._http_client.aclose()
        await self.tb_client.close()
        logger.info("Device sync service stopped")

    async def sync_device(self, iotix_device_id: str) -> str:
        """Sync an IoTix device to ThingsBoard.

        Args:
            iotix_device_id: IoTix device ID

        Returns:
            ThingsBoard device ID
        """
        if not self._http_client:
            raise RuntimeError("Sync service not started")

        # Get device from IoTix
        response = await self._http_client.get(f"/api/v1/devices/{iotix_device_id}")
        response.raise_for_status()
        iotix_device = response.json()

        # Check if already synced
        tb_device = await self.tb_client.get_device_by_name(iotix_device_id)
        if tb_device:
            tb_device_id = tb_device["id"]["id"]
            self._device_mapping[iotix_device_id] = tb_device_id
            return tb_device_id

        # Create in ThingsBoard
        tb_device = await self.tb_client.create_device(
            name=iotix_device_id,
            device_type=iotix_device.get("modelId", "default"),
            additional_info={
                "iotixDeviceId": iotix_device_id,
                "iotixModelId": iotix_device.get("modelId"),
                "syncedAt": asyncio.get_event_loop().time(),
            },
        )
        tb_device_id = tb_device["id"]["id"]
        self._device_mapping[iotix_device_id] = tb_device_id
        logger.info(f"Synced device {iotix_device_id} to ThingsBoard as {tb_device_id}")
        return tb_device_id

    async def forward_telemetry(
        self,
        iotix_device_id: str,
        telemetry: dict[str, Any],
    ) -> None:
        """Forward telemetry from IoTix device to ThingsBoard.

        Args:
            iotix_device_id: IoTix device ID
            telemetry: Telemetry data
        """
        tb_device_id = self._device_mapping.get(iotix_device_id)
        if not tb_device_id:
            tb_device_id = await self.sync_device(iotix_device_id)

        await self.tb_client.send_telemetry(tb_device_id, telemetry)

    async def unsync_device(self, iotix_device_id: str) -> None:
        """Remove device sync with ThingsBoard.

        Args:
            iotix_device_id: IoTix device ID
        """
        tb_device_id = self._device_mapping.pop(iotix_device_id, None)
        if tb_device_id:
            await self.tb_client.delete_device(tb_device_id)
            logger.info(f"Removed ThingsBoard device {tb_device_id}")
