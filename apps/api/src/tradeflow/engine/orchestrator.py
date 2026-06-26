"""Copy orchestrator — hot path for leader event processing."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import (
    CopyEventAction,
    CopyEventResult,
    CopyGroupStatus,
    ExecutionLogStatus,
)
from tradeflow.db.models.copy_trading import (
    CopyEvent,
    CopyGroup,
    CopyGroupFollower,
    ExecutionLog,
)
from tradeflow.db.models.risk import RiskRule
from tradeflow.db.models.trading import TradingAccount
from tradeflow.engine.executor import CopyExecutor
from tradeflow.engine.mapping import TradeMappingStore
from tradeflow.engine.matching import OrderMatcher
from tradeflow.engine.retry_queue import RetryQueue
from tradeflow.engine.types import (
    CopyDecision,
    CopyExecutionResult,
    FollowerContext,
    LeaderEvent,
)
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.notifications.dispatcher import NotificationDispatcher
from tradeflow.risk.evaluator import RiskEvaluator
from tradeflow.risk.types import ProposedOrder

logger = get_logger(__name__)


class CopyOrchestrator:
    """Coordinates dedupe → plan → parallel execute → audit → retry."""

    def __init__(
        self,
        session_manager: BrokerSessionManager,
        mapping_store: TradeMappingStore,
        retry_queue: RetryQueue,
        *,
        max_parallel_followers: int = 10,
        risk_evaluator: RiskEvaluator | None = None,
        notification_dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self._sessions = session_manager
        self._mapping = mapping_store
        self._retry = retry_queue
        self._matcher = OrderMatcher()
        self._executor = CopyExecutor(session_manager)
        self._max_parallel = max_parallel_followers
        self._risk = risk_evaluator
        self._notifications = notification_dispatcher

    async def handle_leader_event(
        self,
        db: AsyncSession,
        event: LeaderEvent,
    ) -> list[CopyExecutionResult]:
        """Main entry point — ultra-low latency hot path."""
        start_ms = time.perf_counter()

        if await self._mapping.is_duplicate(event.id):
            logger.debug("leader_event_deduped", event_id=event.id)
            return []

        group = await self._load_group(db, event.copy_group_id)
        if group is None or group.status != CopyGroupStatus.ACTIVE or not group.copying_enabled:
            return []

        followers = [f for f in group.followers if f.deleted_at is None]
        contexts = await self._build_contexts(db, followers)

        mapping_lookup: dict[tuple[str, UUID], str] = {}
        if event.leader_order_id:
            mapping_lookup = await self._mapping.build_lookup(
                db,
                event.copy_group_id,
                event.leader_order_id,
            )

        decisions = self._matcher.plan_copies(
            event,
            group,
            followers,
            contexts,
            mapping_lookup,
        )

        if not decisions:
            return []

        semaphore = asyncio.Semaphore(self._max_parallel)
        results = await asyncio.gather(
            *[
                self._execute_with_semaphore(
                    semaphore,
                    db,
                    event,
                    decision,
                    contexts.get(decision.follower_account_id),
                    mapping_lookup,
                )
                for decision in decisions
            ],
            return_exceptions=False,
        )

        total_latency = int((time.perf_counter() - start_ms) * 1000)
        await self._persist_audit(db, event, results, total_latency)
        await db.flush()

        logger.info(
            "leader_event_processed",
            event_id=event.id,
            copy_group_id=str(event.copy_group_id),
            followers=len(decisions),
            latency_ms=total_latency,
        )
        return results

    async def retry_execution(
        self,
        db: AsyncSession,
        execution_log_id: UUID,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext,
    ) -> CopyExecutionResult:
        """Retry a previously failed copy execution."""
        log = await db.get(ExecutionLog, execution_log_id)
        if log is None:
            msg = f"ExecutionLog {execution_log_id} not found"
            raise ValueError(msg)

        log.status = ExecutionLogStatus.PROCESSING
        log.attempt += 1
        await db.flush()

        mapping_lookup = await self._mapping.build_lookup(
            db,
            event.copy_group_id,
            event.leader_order_id,
        )
        mapped_id = mapping_lookup.get((event.leader_order_id, decision.follower_account_id))

        result = await self._executor.execute(
            db,
            event,
            decision,
            ctx,
            mapped_follower_order_id=mapped_id,
        )

        if result.success:
            log.status = ExecutionLogStatus.SUCCESS
            log.completed_at = datetime.now(tz=UTC)
            log.latency_ms = result.latency_ms
            if result.decision.action == CopyEventAction.PLACE and result.follower_order_id:
                await self._mapping.store_mapping(
                    db,
                    copy_group_id=event.copy_group_id,
                    leader_order_id=event.leader_order_id,
                    follower_account_id=decision.follower_account_id,
                    follower_order_id=result.follower_order_id,
                    leg_type=decision.leg_type,
                    follower_order_db_id=result.follower_order_db_id,
                )
        else:
            log.status = ExecutionLogStatus.RETRY_SCHEDULED
            log.error_message = result.error
            enqueue_status = await self._retry.enqueue(
                execution_log_id=execution_log_id,
                payload={"event_id": event.id, "decision": self._decision_to_dict(decision)},
                attempt=log.attempt,
            )
            if enqueue_status == "dead_letter":
                await self._notify_trade_failed(db, event, decision, result.error)

        await db.flush()
        return result

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
        ctx: FollowerContext | None,
        mapping_lookup: dict[tuple[str, UUID], str],
    ) -> CopyExecutionResult:
        async with semaphore:
            if ctx is None:
                return CopyExecutionResult(
                    decision=decision,
                    success=False,
                    error="missing_context",
                )

            if decision.skip:
                return CopyExecutionResult(
                    decision=decision,
                    success=False,
                    error=decision.skip_reason,
                )

            risk_block = await self._check_risk(db, event, decision)
            if risk_block is not None:
                return risk_block

            mapped_id = mapping_lookup.get((event.leader_order_id, decision.follower_account_id))
            result = await self._executor.execute(
                db,
                event,
                decision,
                ctx,
                mapped_follower_order_id=mapped_id,
            )

            if not result.success:
                enqueue_status = await self._schedule_retry(db, event, decision, result)
                if enqueue_status == "dead_letter":
                    await self._notify_trade_failed(
                        db,
                        event,
                        decision,
                        result.error or "copy_failed",
                    )
                return result

            if decision.action == CopyEventAction.PLACE and result.follower_order_id:
                await self._mapping.store_mapping(
                    db,
                    copy_group_id=event.copy_group_id,
                    leader_order_id=event.leader_order_id,
                    follower_account_id=decision.follower_account_id,
                    follower_order_id=result.follower_order_id,
                    leg_type=decision.leg_type,
                    follower_order_db_id=result.follower_order_db_id,
                )

            await self._mapping.publish_event(
                event.user_id,
                {
                    "type": "copy_executed",
                    "copy_group_id": str(event.copy_group_id),
                    "follower_account_id": str(decision.follower_account_id),
                    "symbol": event.symbol,
                    "action": decision.action.value,
                    "success": result.success,
                    "latency_ms": result.latency_ms,
                },
            )
            if result.success and self._notifications is not None:
                await self._notifications.notify_trade_copied(
                    db,
                    user_id=event.user_id,
                    symbol=event.symbol,
                    action=decision.action.value,
                    follower_account_id=decision.follower_account_id,
                    copy_group_id=event.copy_group_id,
                    latency_ms=result.latency_ms,
                )
            return result

    async def _schedule_retry(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
        result: CopyExecutionResult,
    ) -> str:
        log = ExecutionLog(
            user_id=event.user_id,
            copy_group_id=event.copy_group_id,
            follower_account_id=decision.follower_account_id,
            leader_event_id=event.id,
            leader_order_id=event.leader_order_id,
            action=decision.action,
            status=ExecutionLogStatus.RETRY_SCHEDULED,
            attempt=1,
            payload={"event_id": event.id, "decision": self._decision_to_dict(decision)},
            error_message=result.error,
            latency_ms=result.latency_ms,
        )
        db.add(log)
        await db.flush()

        return await self._retry.enqueue(
            execution_log_id=log.id,
            payload={"event_id": event.id, "decision": self._decision_to_dict(decision)},
            attempt=1,
        )

    async def _notify_trade_failed(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
        error: str,
    ) -> None:
        if self._notifications is None:
            return
        await self._notifications.notify_trade_failed(
            db,
            user_id=event.user_id,
            symbol=event.symbol,
            error=error,
            copy_group_id=event.copy_group_id,
            follower_account_id=decision.follower_account_id,
        )

    async def _persist_audit(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        results: list[CopyExecutionResult],
        total_latency_ms: int,
    ) -> None:
        for result in results:
            if result.decision.skip:
                result_type = CopyEventResult.SKIPPED
            elif result.success:
                result_type = CopyEventResult.SUCCESS
            elif result.error and "retry" in (result.error or "").lower():
                result_type = CopyEventResult.RETRYING
            else:
                result_type = CopyEventResult.FAILURE

            slippage = None
            if event.price and result.follower_price:
                slippage = abs(result.follower_price - event.price)

            copy_event = CopyEvent(
                user_id=event.user_id,
                copy_group_id=event.copy_group_id,
                leader_account_id=event.leader_account_id,
                follower_account_id=result.decision.follower_account_id,
                leader_event_id=event.id,
                leader_order_id=event.leader_order_id,
                follower_order_id=result.follower_order_id,
                action=result.decision.action,
                result=result_type,
                symbol=event.symbol,
                quantity=result.decision.quantity,
                leader_price=event.price,
                follower_price=result.follower_price,
                slippage=slippage,
                latency_ms=result.latency_ms or total_latency_ms,
                error_message=result.error,
                metadata_={
                    "partial_fill": result.partial_fill,
                    "filled_quantity": result.filled_quantity,
                    "skip_reason": result.decision.skip_reason,
                },
            )
            db.add(copy_event)

    async def _load_group(self, db: AsyncSession, group_id: UUID) -> CopyGroup | None:
        return await db.scalar(
            select(CopyGroup)
            .options(selectinload(CopyGroup.followers))
            .where(CopyGroup.id == group_id, CopyGroup.deleted_at.is_(None)),
        )

    async def _build_contexts(
        self,
        db: AsyncSession,
        followers: list[CopyGroupFollower],
    ) -> dict[UUID, FollowerContext]:
        account_ids = [f.follower_account_id for f in followers]
        if not account_ids:
            return {}

        accounts = await db.scalars(
            select(TradingAccount).where(TradingAccount.id.in_(account_ids)),
        )
        account_map = {a.id: a for a in accounts.all()}

        contexts: dict[UUID, FollowerContext] = {}
        for follower in followers:
            account = account_map.get(follower.follower_account_id)
            if account is None:
                continue
            contexts[follower.follower_account_id] = FollowerContext(
                follower_account_id=follower.follower_account_id,
                broker_connection_id=account.broker_connection_id,
                external_account_id=account.external_account_id,
                copy_mode=follower.copy_mode,
                sizing_value=follower.sizing_value,
                enabled=follower.enabled,
                status=follower.status.value,
                follower_balance=account.balance,
            )
        return contexts

    async def _check_risk(
        self,
        db: AsyncSession,
        event: LeaderEvent,
        decision: CopyDecision,
    ) -> CopyExecutionResult | None:
        if self._risk is None or decision.action != CopyEventAction.PLACE:
            return None

        rule = await db.scalar(
            select(RiskRule).where(
                RiskRule.trading_account_id == decision.follower_account_id,
                RiskRule.deleted_at.is_(None),
            ),
        )
        if rule is None or not rule.enabled:
            return None

        order = ProposedOrder(
            symbol=event.symbol,
            side=decision.side,
            quantity=decision.quantity,
            price=decision.price,
            notional_usd=decision.price * decision.quantity if decision.price else None,
        )
        result = await self._risk.check_pre_trade(rule, decision.follower_account_id, order)
        if result.allowed:
            return None

        violation = result.primary_violation
        reason = violation.message if violation else "risk_blocked"
        return CopyExecutionResult(
            decision=decision,
            success=False,
            error=f"risk_blocked:{reason}",
        )

    @staticmethod
    def _decision_to_dict(decision: CopyDecision) -> dict[str, object]:
        return {
            "follower_account_id": str(decision.follower_account_id),
            "follower_config_id": str(decision.follower_config_id),
            "action": decision.action.value,
            "quantity": decision.quantity,
            "side": decision.side.value,
            "order_type": decision.order_type.value,
            "price": str(decision.price) if decision.price else None,
            "stop_price": str(decision.stop_price) if decision.stop_price else None,
            "leg_type": decision.leg_type.value,
        }
