"""Risk alert system — in-app notifications + Redis pub/sub."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import NotificationType, RiskAction
from tradeflow.db.models.notification import Notification
from tradeflow.db.models.risk import RiskBreach
from tradeflow.risk.state import RiskStateStore
from tradeflow.risk.types import RiskViolation

logger = get_logger(__name__)


class RiskAlertService:
    """Delivers risk alerts via notifications and real-time channels."""

    def __init__(self, state_store: RiskStateStore) -> None:
        self._state = state_store

    async def send_breach_alert(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        breach: RiskBreach,
    ) -> Notification:
        title = f"Risk Breach: {breach.breach_type.value.replace('_', ' ').title()}"
        body = breach.message
        if breach.action_taken != RiskAction.BLOCK:
            body += f" — Action: {breach.action_taken.value.replace('_', ' ')}"

        notification = Notification(
            user_id=user_id,
            type=NotificationType.RISK_BREACH,
            title=title,
            body=body,
            action_url=f"/dashboard/risk?account={breach.trading_account_id}",
            metadata_={
                "breach_id": str(breach.id),
                "breach_type": breach.breach_type.value,
                "action_taken": breach.action_taken.value,
                "account_id": str(breach.trading_account_id),
            },
        )
        db.add(notification)
        await db.flush()

        await self._state.publish_status(
            user_id,
            {
                "type": "notification",
                "notification_type": NotificationType.RISK_BREACH.value,
                "title": title,
                "body": body,
                "breach_id": str(breach.id),
            },
        )
        logger.info("risk_alert_sent", user_id=str(user_id), breach_id=str(breach.id))
        return notification

    async def send_kill_switch_alert(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        account_id: UUID,
        activated: bool,
    ) -> Notification:
        title = "Kill Switch Activated" if activated else "Kill Switch Deactivated"
        body = (
            "All trading and copying has been halted."
            if activated
            else "Trading and copying may resume."
        )

        notification = Notification(
            user_id=user_id,
            type=NotificationType.KILL_SWITCH,
            title=title,
            body=body,
            action_url=f"/dashboard/risk?account={account_id}",
            metadata_={"account_id": str(account_id), "activated": activated},
        )
        db.add(notification)
        await db.flush()

        await self._state.publish_status(
            user_id,
            {
                "type": "notification",
                "notification_type": NotificationType.KILL_SWITCH.value,
                "title": title,
                "body": body,
            },
        )
        return notification

    async def send_warning(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        account_id: UUID,
        violation: RiskViolation,
    ) -> None:
        await self._state.publish_status(
            user_id,
            {
                "type": "risk_warning",
                "account_id": str(account_id),
                "breach_type": violation.breach_type.value,
                "message": violation.message,
            },
        )
