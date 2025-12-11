"""Tests for the Device Engine API."""

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptimeSeconds" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness endpoint."""
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    """Test list models endpoint."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_register_model(client: AsyncClient):
    """Test register model endpoint."""
    model = {
        "id": "test-model",
        "name": "Test Model",
        "type": "sensor",
        "protocol": "mqtt",
    }
    response = await client.post("/api/v1/models", json=model)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-model"


@pytest.mark.asyncio
async def test_get_model_not_found(client: AsyncClient):
    """Test get model returns 404 for unknown model."""
    response = await client.get("/api/v1/models/unknown-model")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient):
    """Test list devices endpoint."""
    response = await client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_create_device_invalid_model(client: AsyncClient):
    """Test create device with invalid model returns 400."""
    response = await client.post(
        "/api/v1/devices",
        json={"modelId": "non-existent-model"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_device_not_found(client: AsyncClient):
    """Test get device returns 404 for unknown device."""
    response = await client.get("/api/v1/devices/unknown-device")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_stats(client: AsyncClient):
    """Test stats endpoint."""
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_devices" in data
    assert "running_devices" in data
    assert "total_models" in data
