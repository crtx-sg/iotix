"""Tests for the Management API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from src.main import app, users, sessions, generate_token
from src.models import User, UserRole, UserStatus


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    # Clear and setup test data
    users.clear()
    sessions.clear()

    # Create test admin user
    admin_id = "test-admin"
    users[admin_id] = User(
        id=admin_id,
        email="admin@iotix.local",
        name="Test Administrator",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """Create authenticated test client with admin user."""
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@iotix.local", "password": "admin"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
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
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@iotix.local", "password": "admin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expires_at" in data
    assert data["user"]["email"] == "admin@iotix.local"


@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    """Test login with invalid email."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "invalid@example.com", "password": "password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test get current user without authentication."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(auth_client: AsyncClient):
    """Test get current user with authentication."""
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@iotix.local"


@pytest.mark.asyncio
async def test_list_users_unauthorized(client: AsyncClient):
    """Test list users without authentication."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_authenticated(auth_client: AsyncClient):
    """Test list users with authentication."""
    response = await auth_client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_tenants_authenticated(auth_client: AsyncClient):
    """Test list tenants with authentication."""
    response = await auth_client.get("/api/v1/tenants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_user_not_found(auth_client: AsyncClient):
    """Test get user returns 404 for unknown user."""
    response = await auth_client.get("/api/v1/users/unknown-user")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tenant_not_found(auth_client: AsyncClient):
    """Test get tenant returns 404 for unknown tenant."""
    response = await auth_client.get("/api/v1/tenants/unknown-tenant")
    assert response.status_code == 404
