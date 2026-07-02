"""Persist structured log entries for the admin System Logs page."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.db.enums import SystemLogLevel
from tradeflow.db.models.admin_ops import SystemLogEntry


async def record_system_log(
    db: AsyncSession,
    *,
    level: SystemLogLevel | str,
    source: str,
    message: str,
    user_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> SystemLogEntry:
    resolved_level = SystemLogLevel(level) if isinstance(level, str) else level
    entry = SystemLogEntry(
        level=resolved_level,
        source=source,
        message=message,
        user_id=user_id,
        metadata_=metadata,
        created_at=datetime.now(tz=UTC),
    )
    db.add(entry)
    await db.flush()
    return entry
