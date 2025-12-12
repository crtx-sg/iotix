"""Tests for the Test Engine API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app, test_suites, test_runs, schedules


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    # Clear test data before each test
    test_suites.clear()
    test_runs.clear()
    schedules.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Health endpoints
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptimeSeconds" in data
    assert "activeSuites" in data
    assert "activeRuns" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness endpoint."""
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


# Test Suite endpoints
@pytest.mark.asyncio
async def test_list_suites_empty(client: AsyncClient):
    """Test list suites returns empty list initially."""
    response = await client.get("/api/v1/suites")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_suite(client: AsyncClient):
    """Test creating a test suite."""
    suite_data = {
        "name": "Device Integration Tests",
        "description": "Tests for device integration",
        "testCases": ["test_create_device", "test_start_device"],
        "tags": ["integration", "devices"],
        "timeoutSeconds": 1800,
    }
    response = await client.post("/api/v1/suites", json=suite_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Device Integration Tests"
    assert data["testCases"] == ["test_create_device", "test_start_device"]


@pytest.mark.asyncio
async def test_get_suite(client: AsyncClient):
    """Test getting a test suite by ID."""
    # Create suite first
    suite_data = {
        "name": "Test Suite",
        "testCases": ["test_1"],
    }
    create_response = await client.post("/api/v1/suites", json=suite_data)
    suite_id = create_response.json()["id"]

    # Get suite
    response = await client.get(f"/api/v1/suites/{suite_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Suite"


@pytest.mark.asyncio
async def test_get_suite_not_found(client: AsyncClient):
    """Test getting a non-existent suite returns 404."""
    response = await client.get("/api/v1/suites/unknown-suite")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_suite(client: AsyncClient):
    """Test deleting a test suite."""
    # Create suite first
    suite_data = {
        "name": "Suite to Delete",
        "testCases": ["test_1"],
    }
    create_response = await client.post("/api/v1/suites", json=suite_data)
    suite_id = create_response.json()["id"]

    # Delete suite
    response = await client.delete(f"/api/v1/suites/{suite_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/suites/{suite_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_suite_not_found(client: AsyncClient):
    """Test deleting a non-existent suite returns 404."""
    response = await client.delete("/api/v1/suites/unknown-suite")
    assert response.status_code == 404


# Test Run endpoints
@pytest.mark.asyncio
async def test_list_runs_empty(client: AsyncClient):
    """Test list runs returns empty list initially."""
    response = await client.get("/api/v1/runs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_run(client: AsyncClient):
    """Test creating a test run."""
    run_data = {
        "testCases": ["test_device_creation"],
        "variables": {"timeout": 30},
        "tags": ["smoke"],
    }
    response = await client.post("/api/v1/runs", json=run_data)
    assert response.status_code == 201
    data = response.json()
    assert "runId" in data
    assert data["status"] in ["pending", "running"]
    assert "startedAt" in data


@pytest.mark.asyncio
async def test_get_run(client: AsyncClient):
    """Test getting a test run by ID."""
    # Create run first
    run_data = {"testCases": ["test_1"]}
    create_response = await client.post("/api/v1/runs", json=run_data)
    run_id = create_response.json()["runId"]

    # Get run
    response = await client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["runId"] == run_id


@pytest.mark.asyncio
async def test_get_run_not_found(client: AsyncClient):
    """Test getting a non-existent run returns 404."""
    response = await client.get("/api/v1/runs/unknown-run")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_run_not_found(client: AsyncClient):
    """Test cancelling a non-existent run returns 404."""
    response = await client.post("/api/v1/runs/unknown-run/cancel")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_run_report_json(client: AsyncClient):
    """Test getting a test run report in JSON format."""
    # Create run first
    run_data = {"testCases": ["test_1"]}
    create_response = await client.post("/api/v1/runs", json=run_data)
    run_id = create_response.json()["runId"]

    # Get report
    response = await client.get(f"/api/v1/runs/{run_id}/report?format=json")
    assert response.status_code == 200
    assert "runId" in response.json()


@pytest.mark.asyncio
async def test_get_run_report_not_found(client: AsyncClient):
    """Test getting report for non-existent run returns 404."""
    response = await client.get("/api/v1/runs/unknown-run/report")
    assert response.status_code == 404


# Schedule endpoints
@pytest.mark.asyncio
async def test_list_schedules_empty(client: AsyncClient):
    """Test list schedules returns empty list initially."""
    response = await client.get("/api/v1/schedules")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_schedule(client: AsyncClient):
    """Test creating a scheduled test execution."""
    schedule_data = {
        "cron": "0 0 * * *",
        "suiteId": "suite-123",
        "enabled": True,
    }
    response = await client.post("/api/v1/schedules", json=schedule_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["cron"] == "0 0 * * *"
    assert data["suiteId"] == "suite-123"


@pytest.mark.asyncio
async def test_delete_schedule(client: AsyncClient):
    """Test deleting a schedule."""
    # Create schedule first
    schedule_data = {
        "cron": "0 0 * * *",
        "suiteId": "suite-123",
    }
    create_response = await client.post("/api/v1/schedules", json=schedule_data)
    schedule_id = create_response.json()["id"]

    # Delete schedule
    response = await client.delete(f"/api/v1/schedules/{schedule_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_schedule_not_found(client: AsyncClient):
    """Test deleting a non-existent schedule returns 404."""
    response = await client.delete("/api/v1/schedules/unknown-schedule")
    assert response.status_code == 404


# Webhook endpoint
@pytest.mark.asyncio
async def test_webhook_trigger(client: AsyncClient):
    """Test webhook trigger creates a test run."""
    run_data = {
        "testCases": ["test_webhook"],
        "tags": ["ci"],
    }
    response = await client.post("/api/v1/webhook", json=run_data)
    assert response.status_code == 200  # Webhook returns 200, not 201
    assert "runId" in response.json()
