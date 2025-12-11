"""Management API - FastAPI application for administration and user management."""

import hashlib
import logging
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from . import __version__
from .audit import AuditService, get_audit_service
from .models import (
    User,
    UserCreate,
    UserUpdate,
    UserRole,
    UserStatus,
    Tenant,
    TenantCreate,
    TenantUpdate,
    AuditAction,
    AuditResource,
    AuditLog,
    ResourceQuota,
    ApiKey,
    ApiKeyCreate,
    Permission,
    ROLE_PERMISSIONS,
)


# Configuration
class Settings(BaseSettings):
    service_name: str = "management-api"
    service_port: int = 8082
    log_level: str = "INFO"
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_hours: int = 24
    device_engine_url: str = "http://localhost:8080"
    test_engine_url: str = "http://localhost:8081"
    thingsboard_url: str = ""
    thingsboard_username: str = ""
    thingsboard_password: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Track startup time
start_time = time.time()

# In-memory storage (would be a database in production)
users: dict[str, User] = {}
tenants: dict[str, Tenant] = {}
api_keys: dict[str, tuple[str, ApiKey]] = {}  # key_hash -> (key, ApiKey)
sessions: dict[str, dict[str, Any]] = {}  # token -> session data

# Security
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure token."""
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"iotix_{secrets.token_urlsafe(32)}"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """Get current authenticated user from token or API key."""
    # Check for Bearer token
    if credentials:
        token = credentials.credentials
        session = sessions.get(token)
        if session:
            user_id = session.get("user_id")
            if user_id and user_id in users:
                return users[user_id]

    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash in api_keys:
            _, api_key_obj = api_keys[key_hash]
            if api_key_obj.user_id in users:
                return users[api_key_obj.user_id]

    raise HTTPException(status_code=401, detail="Not authenticated")


def check_permission(user: User, permission: Permission) -> None:
    """Check if user has a specific permission."""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    if Permission.ADMIN not in user_permissions and permission not in user_permissions:
        raise HTTPException(status_code=403, detail="Permission denied")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Management API...")

    # Create default admin user if none exists
    if not users:
        admin_id = f"user-{uuid4().hex[:8]}"
        users[admin_id] = User(
            id=admin_id,
            email="admin@iotix.local",
            name="Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        logger.info(f"Created default admin user: admin@iotix.local")

    yield
    logger.info("Management API shutdown complete")


app = FastAPI(
    title="IoTix Management API",
    description="Administration and user management for IoTix platform",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Check service health."""
    return {
        "status": "healthy",
        "version": __version__,
        "uptimeSeconds": time.time() - start_time,
        "users": len(users),
        "tenants": len(tenants),
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """Check if service is ready."""
    return {"status": "ready"}


# Auth endpoints
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: datetime
    user: User


@app.post("/api/v1/auth/login", tags=["Auth"])
async def login(
    request: LoginRequest,
    audit: AuditService = Depends(get_audit_service),
) -> LoginResponse:
    """Login and get authentication token."""
    # Find user by email (in production, verify password hash)
    user = next((u for u in users.values() if u.email == request.email), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account is not active")

    # Create session
    token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    sessions[token] = {
        "user_id": user.id,
        "expires_at": expires_at,
    }

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Audit log
    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.LOGIN,
        resource=AuditResource.USER,
        resource_id=user.id,
    )

    return LoginResponse(token=token, expires_at=expires_at, user=user)


@app.post("/api/v1/auth/logout", tags=["Auth"])
async def logout(
    user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    audit: AuditService = Depends(get_audit_service),
) -> dict[str, str]:
    """Logout and invalidate token."""
    if credentials:
        sessions.pop(credentials.credentials, None)

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.LOGOUT,
        resource=AuditResource.USER,
        resource_id=user.id,
    )

    return {"status": "logged out"}


@app.get("/api/v1/auth/me", tags=["Auth"])
async def get_me(user: User = Depends(get_current_user)) -> User:
    """Get current user info."""
    return user


# User management endpoints
@app.get("/api/v1/users", tags=["Users"])
async def list_users(
    role: UserRole | None = None,
    status: UserStatus | None = None,
    tenant_id: str | None = Query(None, alias="tenantId"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
) -> list[User]:
    """List users."""
    check_permission(user, Permission.USERS_READ)

    result = list(users.values())
    if role:
        result = [u for u in result if u.role == role]
    if status:
        result = [u for u in result if u.status == status]
    if tenant_id:
        result = [u for u in result if u.tenant_id == tenant_id]

    return result[offset : offset + limit]


@app.post("/api/v1/users", status_code=201, tags=["Users"])
async def create_user(
    request: UserCreate,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> User:
    """Create a new user."""
    check_permission(user, Permission.USERS_WRITE)

    # Check email uniqueness
    if any(u.email == request.email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already exists")

    user_id = f"user-{uuid4().hex[:8]}"
    new_user = User(
        id=user_id,
        email=request.email,
        name=request.name,
        role=request.role,
        tenant_id=request.tenant_id,
        created_at=datetime.now(timezone.utc),
    )
    users[user_id] = new_user

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.CREATE,
        resource=AuditResource.USER,
        resource_id=user_id,
        details={"email": request.email, "role": request.role.value},
    )

    return new_user


@app.get("/api/v1/users/{user_id}", tags=["Users"])
async def get_user(
    user_id: str,
    user: User = Depends(get_current_user),
) -> User:
    """Get user by ID."""
    check_permission(user, Permission.USERS_READ)

    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.patch("/api/v1/users/{user_id}", tags=["Users"])
async def update_user(
    user_id: str,
    request: UserUpdate,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> User:
    """Update a user."""
    check_permission(user, Permission.USERS_WRITE)

    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    target_user = users[user_id]
    update_data = request.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(target_user, key, value)
    target_user.updated_at = datetime.now(timezone.utc)

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.UPDATE,
        resource=AuditResource.USER,
        resource_id=user_id,
        details=update_data,
    )

    return target_user


@app.delete("/api/v1/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(
    user_id: str,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> None:
    """Delete a user."""
    check_permission(user, Permission.USERS_DELETE)

    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    del users[user_id]

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.DELETE,
        resource=AuditResource.USER,
        resource_id=user_id,
    )


# Tenant management endpoints
@app.get("/api/v1/tenants", tags=["Tenants"])
async def list_tenants(
    limit: int = Query(50, ge=1, le=500),
    user: User = Depends(get_current_user),
) -> list[Tenant]:
    """List all tenants."""
    check_permission(user, Permission.TENANTS_READ)
    return list(tenants.values())[:limit]


@app.post("/api/v1/tenants", status_code=201, tags=["Tenants"])
async def create_tenant(
    request: TenantCreate,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> Tenant:
    """Create a new tenant."""
    check_permission(user, Permission.TENANTS_WRITE)

    tenant_id = f"tenant-{uuid4().hex[:8]}"
    tenant = Tenant(
        id=tenant_id,
        name=request.name,
        description=request.description,
        quota=request.quota or {},
        created_at=datetime.now(timezone.utc),
    )
    tenants[tenant_id] = tenant

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.CREATE,
        resource=AuditResource.TENANT,
        resource_id=tenant_id,
        details={"name": request.name},
    )

    return tenant


@app.get("/api/v1/tenants/{tenant_id}", tags=["Tenants"])
async def get_tenant(
    tenant_id: str,
    user: User = Depends(get_current_user),
) -> Tenant:
    """Get tenant by ID."""
    check_permission(user, Permission.TENANTS_READ)

    if tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenants[tenant_id]


@app.patch("/api/v1/tenants/{tenant_id}", tags=["Tenants"])
async def update_tenant(
    tenant_id: str,
    request: TenantUpdate,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> Tenant:
    """Update a tenant."""
    check_permission(user, Permission.TENANTS_WRITE)

    if tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant = tenants[tenant_id]
    update_data = request.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tenant, key, value)
    tenant.updated_at = datetime.now(timezone.utc)

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.UPDATE,
        resource=AuditResource.TENANT,
        resource_id=tenant_id,
        details=update_data,
    )

    return tenant


@app.delete("/api/v1/tenants/{tenant_id}", status_code=204, tags=["Tenants"])
async def delete_tenant(
    tenant_id: str,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> None:
    """Delete a tenant."""
    check_permission(user, Permission.TENANTS_DELETE)

    if tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check for users in tenant
    tenant_users = [u for u in users.values() if u.tenant_id == tenant_id]
    if tenant_users:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete tenant with {len(tenant_users)} users",
        )

    del tenants[tenant_id]

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.DELETE,
        resource=AuditResource.TENANT,
        resource_id=tenant_id,
    )


@app.get("/api/v1/tenants/{tenant_id}/quota", tags=["Tenants"])
async def get_tenant_quota(
    tenant_id: str,
    user: User = Depends(get_current_user),
) -> ResourceQuota:
    """Get tenant resource quota and usage."""
    check_permission(user, Permission.TENANTS_READ)

    if tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant = tenants[tenant_id]
    tenant_users = [u for u in users.values() if u.tenant_id == tenant_id]

    return ResourceQuota(
        tenant_id=tenant_id,
        max_devices=tenant.quota.get("maxDevices", 1000),
        max_groups=tenant.quota.get("maxGroups", 100),
        max_models=tenant.quota.get("maxModels", 50),
        max_users=tenant.quota.get("maxUsers", 10),
        max_test_runs_per_day=tenant.quota.get("maxTestRunsPerDay", 100),
        current_users=len(tenant_users),
        # Other current values would come from device engine
    )


# API Key management
@app.get("/api/v1/api-keys", tags=["API Keys"])
async def list_api_keys(
    user: User = Depends(get_current_user),
) -> list[ApiKey]:
    """List API keys for current user."""
    return [key for _, key in api_keys.values() if key.user_id == user.id]


@app.post("/api/v1/api-keys", status_code=201, tags=["API Keys"])
async def create_api_key(
    request: ApiKeyCreate,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> dict[str, Any]:
    """Create a new API key."""
    key = generate_api_key()
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

    api_key = ApiKey(
        id=f"apikey-{uuid4().hex[:8]}",
        name=request.name,
        key_prefix=key[:12],
        user_id=user.id,
        tenant_id=user.tenant_id,
        permissions=request.permissions,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )

    api_keys[key_hash] = (key, api_key)

    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.CREATE,
        resource=AuditResource.USER,
        resource_id=api_key.id,
        details={"name": request.name, "type": "api_key"},
    )

    # Return full key only on creation
    return {
        "key": key,
        "apiKey": api_key.model_dump(by_alias=True),
    }


@app.delete("/api/v1/api-keys/{key_id}", status_code=204, tags=["API Keys"])
async def delete_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> None:
    """Delete an API key."""
    # Find and delete key
    for key_hash, (_, api_key) in list(api_keys.items()):
        if api_key.id == key_id and api_key.user_id == user.id:
            del api_keys[key_hash]
            audit.log(
                user_id=user.id,
                user_email=user.email,
                action=AuditAction.DELETE,
                resource=AuditResource.USER,
                resource_id=key_id,
                details={"type": "api_key"},
            )
            return

    raise HTTPException(status_code=404, detail="API key not found")


# Audit log endpoints
@app.get("/api/v1/audit-logs", tags=["Audit"])
async def list_audit_logs(
    user_id: str | None = Query(None, alias="userId"),
    tenant_id: str | None = Query(None, alias="tenantId"),
    action: AuditAction | None = None,
    resource: AuditResource | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> list[AuditLog]:
    """Query audit logs."""
    check_permission(user, Permission.AUDIT_READ)

    return audit.query(
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource=resource,
        limit=limit,
        offset=offset,
    )


@app.get("/api/v1/audit-logs/export", tags=["Audit"])
async def export_audit_logs(
    format: str = Query("json", enum=["json", "csv"]),
    user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
) -> str:
    """Export audit logs."""
    from fastapi.responses import PlainTextResponse

    check_permission(user, Permission.AUDIT_READ)

    # Log the export action
    audit.log(
        user_id=user.id,
        user_email=user.email,
        action=AuditAction.EXPORT,
        resource=AuditResource.USER,
        resource_id="audit-logs",
        details={"format": format},
    )

    content = audit.export(format=format)
    media_type = "application/json" if format == "json" else "text/csv"

    return PlainTextResponse(content=content, media_type=media_type)
