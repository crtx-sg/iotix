"""Audit logging service for IoTix."""

import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import AuditAction, AuditLog, AuditResource

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging operations.

    Stores audit logs in memory by default.
    Can be extended to use a database or external service.
    """

    def __init__(self, max_logs: int = 10000):
        """Initialize audit service.

        Args:
            max_logs: Maximum number of logs to keep in memory
        """
        self._logs: list[AuditLog] = []
        self._max_logs = max_logs

    def log(
        self,
        user_id: str,
        user_email: str,
        action: AuditAction,
        resource: AuditResource,
        resource_id: str,
        tenant_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry.

        Args:
            user_id: ID of the user performing the action
            user_email: Email of the user
            action: Action being performed
            resource: Resource being acted upon
            resource_id: ID of the resource
            tenant_id: Optional tenant ID
            details: Optional additional details
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created audit log entry
        """
        log_entry = AuditLog(
            id=f"audit-{uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            user_email=user_email,
            tenant_id=tenant_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._logs.append(log_entry)

        # Trim old logs if over limit
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]

        logger.debug(
            f"Audit: {user_email} {action.value} {resource.value}/{resource_id}"
        )

        return log_entry

    def query(
        self,
        user_id: str | None = None,
        tenant_id: str | None = None,
        action: AuditAction | None = None,
        resource: AuditResource | None = None,
        resource_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit logs with filters.

        Args:
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            action: Filter by action
            resource: Filter by resource type
            resource_id: Filter by resource ID
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of matching audit logs
        """
        results = self._logs.copy()

        if user_id:
            results = [log for log in results if log.user_id == user_id]
        if tenant_id:
            results = [log for log in results if log.tenant_id == tenant_id]
        if action:
            results = [log for log in results if log.action == action]
        if resource:
            results = [log for log in results if log.resource == resource]
        if resource_id:
            results = [log for log in results if log.resource_id == resource_id]
        if start_time:
            results = [log for log in results if log.timestamp >= start_time]
        if end_time:
            results = [log for log in results if log.timestamp <= end_time]

        # Sort by timestamp descending (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)

        return results[offset : offset + limit]

    def get_by_id(self, log_id: str) -> AuditLog | None:
        """Get audit log by ID.

        Args:
            log_id: Audit log ID

        Returns:
            Audit log or None if not found
        """
        for log in self._logs:
            if log.id == log_id:
                return log
        return None

    def count(
        self,
        user_id: str | None = None,
        tenant_id: str | None = None,
        action: AuditAction | None = None,
        resource: AuditResource | None = None,
    ) -> int:
        """Count audit logs matching filters.

        Args:
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            action: Filter by action
            resource: Filter by resource type

        Returns:
            Count of matching logs
        """
        results = self._logs

        if user_id:
            results = [log for log in results if log.user_id == user_id]
        if tenant_id:
            results = [log for log in results if log.tenant_id == tenant_id]
        if action:
            results = [log for log in results if log.action == action]
        if resource:
            results = [log for log in results if log.resource == resource]

        return len(results)

    def export(
        self,
        format: str = "json",
        **filters: Any,
    ) -> str:
        """Export audit logs in specified format.

        Args:
            format: Output format (json, csv)
            **filters: Query filters

        Returns:
            Exported data as string
        """
        logs = self.query(**filters, limit=10000)

        if format == "csv":
            lines = [
                "id,timestamp,user_id,user_email,tenant_id,action,resource,resource_id,ip_address"
            ]
            for log in logs:
                lines.append(
                    f"{log.id},{log.timestamp.isoformat()},{log.user_id},"
                    f"{log.user_email},{log.tenant_id or ''},"
                    f"{log.action.value},{log.resource.value},"
                    f"{log.resource_id},{log.ip_address or ''}"
                )
            return "\n".join(lines)

        # Default to JSON
        import json

        return json.dumps(
            [log.model_dump(by_alias=True, mode="json") for log in logs],
            indent=2,
            default=str,
        )

    def clear(self, before: datetime | None = None) -> int:
        """Clear audit logs.

        Args:
            before: Only clear logs before this time

        Returns:
            Number of logs cleared
        """
        if before:
            original_count = len(self._logs)
            self._logs = [log for log in self._logs if log.timestamp >= before]
            return original_count - len(self._logs)
        else:
            count = len(self._logs)
            self._logs = []
            return count


# Global audit service instance
_audit_service: AuditService | None = None


def get_audit_service() -> AuditService:
    """Get the global audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
