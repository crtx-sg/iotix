"""Pydantic models for Management API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(BaseModel):
    """User model."""
    id: str
    email: str
    name: str
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE
    tenant_id: str | None = Field(None, alias="tenantId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    last_login: datetime | None = Field(None, alias="lastLogin")

    model_config = {"populate_by_name": True}


class UserCreate(BaseModel):
    """User creation request."""
    email: str
    name: str
    password: str
    role: UserRole = UserRole.VIEWER
    tenant_id: str | None = Field(None, alias="tenantId")

    model_config = {"populate_by_name": True}


class UserUpdate(BaseModel):
    """User update request."""
    name: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    tenant_id: str | None = Field(None, alias="tenantId")

    model_config = {"populate_by_name": True}


class Tenant(BaseModel):
    """Tenant model for multi-tenancy."""
    id: str
    name: str
    description: str | None = None
    status: str = "active"
    quota: dict[str, int] = Field(default_factory=lambda: {
        "maxDevices": 1000,
        "maxGroups": 100,
        "maxModels": 50,
    })
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class TenantCreate(BaseModel):
    """Tenant creation request."""
    name: str
    description: str | None = None
    quota: dict[str, int] | None = None


class TenantUpdate(BaseModel):
    """Tenant update request."""
    name: str | None = None
    description: str | None = None
    status: str | None = None
    quota: dict[str, int] | None = None


class AuditAction(str, Enum):
    """Audit log action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    START = "start"
    STOP = "stop"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"


class AuditResource(str, Enum):
    """Audit log resource types."""
    USER = "user"
    TENANT = "tenant"
    DEVICE = "device"
    DEVICE_GROUP = "device_group"
    DEVICE_MODEL = "device_model"
    TEST_RUN = "test_run"
    TEST_SUITE = "test_suite"
    SCHEDULE = "schedule"
    REPORT = "report"


class AuditLog(BaseModel):
    """Audit log entry."""
    id: str
    timestamp: datetime
    user_id: str = Field(alias="userId")
    user_email: str = Field(alias="userEmail")
    tenant_id: str | None = Field(None, alias="tenantId")
    action: AuditAction
    resource: AuditResource
    resource_id: str = Field(alias="resourceId")
    details: dict[str, Any] = {}
    ip_address: str | None = Field(None, alias="ipAddress")
    user_agent: str | None = Field(None, alias="userAgent")

    model_config = {"populate_by_name": True}


class ResourceQuota(BaseModel):
    """Resource quota for a tenant."""
    tenant_id: str = Field(alias="tenantId")
    max_devices: int = Field(1000, alias="maxDevices")
    max_groups: int = Field(100, alias="maxGroups")
    max_models: int = Field(50, alias="maxModels")
    max_users: int = Field(10, alias="maxUsers")
    max_test_runs_per_day: int = Field(100, alias="maxTestRunsPerDay")
    current_devices: int = Field(0, alias="currentDevices")
    current_groups: int = Field(0, alias="currentGroups")
    current_models: int = Field(0, alias="currentModels")
    current_users: int = Field(0, alias="currentUsers")

    model_config = {"populate_by_name": True}


class ApiKey(BaseModel):
    """API key model."""
    id: str
    name: str
    key_prefix: str = Field(alias="keyPrefix")
    user_id: str = Field(alias="userId")
    tenant_id: str | None = Field(None, alias="tenantId")
    permissions: list[str] = []
    created_at: datetime = Field(alias="createdAt")
    expires_at: datetime | None = Field(None, alias="expiresAt")
    last_used: datetime | None = Field(None, alias="lastUsed")

    model_config = {"populate_by_name": True}


class ApiKeyCreate(BaseModel):
    """API key creation request."""
    name: str
    permissions: list[str] = []
    expires_in_days: int | None = Field(None, alias="expiresInDays")

    model_config = {"populate_by_name": True}


class Permission(str, Enum):
    """Permission types."""
    DEVICES_READ = "devices:read"
    DEVICES_WRITE = "devices:write"
    DEVICES_DELETE = "devices:delete"
    MODELS_READ = "models:read"
    MODELS_WRITE = "models:write"
    MODELS_DELETE = "models:delete"
    GROUPS_READ = "groups:read"
    GROUPS_WRITE = "groups:write"
    GROUPS_DELETE = "groups:delete"
    TESTS_READ = "tests:read"
    TESTS_WRITE = "tests:write"
    TESTS_DELETE = "tests:delete"
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    TENANTS_READ = "tenants:read"
    TENANTS_WRITE = "tenants:write"
    TENANTS_DELETE = "tenants:delete"
    AUDIT_READ = "audit:read"
    ADMIN = "admin"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: list(Permission),
    UserRole.OPERATOR: [
        Permission.DEVICES_READ,
        Permission.DEVICES_WRITE,
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.GROUPS_READ,
        Permission.GROUPS_WRITE,
        Permission.TESTS_READ,
        Permission.TESTS_WRITE,
    ],
    UserRole.VIEWER: [
        Permission.DEVICES_READ,
        Permission.MODELS_READ,
        Permission.GROUPS_READ,
        Permission.TESTS_READ,
    ],
}
