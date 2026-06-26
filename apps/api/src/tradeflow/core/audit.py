"""Shared audit logging helper for admin and feature mutations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.db.enums import AuditAction
from tradeflow.db.models.audit import AuditLog


async def record_audit(
    db: AsyncSession,
    *,
    action: AuditAction,
    resource_type: str,
    resource_id: UUID | None = None,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    old_values: dict[str, object] | None = None,
    new_values: dict[str, object] | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        old_values=old_values,
        new_values=new_values,
        metadata_=metadata,
        created_at=datetime.now(tz=UTC),
    )
    db.add(entry)
    await db.flush()
    return entry
