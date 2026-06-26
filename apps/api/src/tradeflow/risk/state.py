"""Redis-backed real-time account risk state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from redis.asyncio import Redis

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import RiskMonitorStatus
from tradeflow.risk.types import AccountRiskState

logger = get_logger(__name__)

STATE_TTL_SECONDS = 86_400 * 7  # 7 days


class RiskStateStore:
    """Persists and retrieves account risk state from Redis."""

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    async def get_state(self, account_id: UUID) -> AccountRiskState:
        key = self._key(account_id)
        raw = await self._redis.get(key)
        if raw is None:
            return AccountRiskState(trading_account_id=account_id)
        data = json.loads(raw)
        return AccountRiskState(
            trading_account_id=account_id,
            daily_pnl=Decimal(str(data.get("daily_pnl", "0"))),
            peak_equity=Decimal(str(data.get("peak_equity", "0"))),
            current_equity=Decimal(str(data.get("current_equity", "0"))),
            drawdown_usd=Decimal(str(data.get("drawdown_usd", "0"))),
            total_open_contracts=int(data.get("total_open_contracts", 0)),
            contracts_by_symbol=data.get("contracts_by_symbol", {}),
            current_leverage=Decimal(str(data.get("current_leverage", "0"))),
            kill_switch_active=bool(data.get("kill_switch_active", False)),
            last_reset_at=(
                datetime.fromisoformat(data["last_reset_at"]) if data.get("last_reset_at") else None
            ),
            status=RiskMonitorStatus(data.get("status", RiskMonitorStatus.HEALTHY.value)),
        )

    async def save_state(self, state: AccountRiskState) -> None:
        key = self._key(state.trading_account_id)
        payload = {
            "daily_pnl": str(state.daily_pnl),
            "peak_equity": str(state.peak_equity),
            "current_equity": str(state.current_equity),
            "drawdown_usd": str(state.drawdown_usd),
            "total_open_contracts": state.total_open_contracts,
            "contracts_by_symbol": state.contracts_by_symbol,
            "current_leverage": str(state.current_leverage),
            "kill_switch_active": state.kill_switch_active,
            "last_reset_at": state.last_reset_at.isoformat() if state.last_reset_at else None,
            "status": state.status.value,
        }
        await self._redis.set(key, json.dumps(payload), ex=STATE_TTL_SECONDS)

    async def update_pnl(
        self,
        account_id: UUID,
        *,
        daily_pnl: Decimal,
        current_equity: Decimal,
    ) -> AccountRiskState:
        state = await self.get_state(account_id)
        state.daily_pnl = daily_pnl
        state.current_equity = current_equity

        if current_equity > state.peak_equity:
            state.peak_equity = current_equity

        state.drawdown_usd = state.peak_equity - current_equity
        await self.save_state(state)
        return state

    async def update_positions(
        self,
        account_id: UUID,
        *,
        contracts_by_symbol: dict[str, int],
        current_leverage: Decimal,
    ) -> AccountRiskState:
        state = await self.get_state(account_id)
        state.contracts_by_symbol = contracts_by_symbol
        state.total_open_contracts = sum(abs(v) for v in contracts_by_symbol.values())
        state.current_leverage = current_leverage
        await self.save_state(state)
        return state

    async def set_kill_switch(self, account_id: UUID, active: bool) -> None:
        state = await self.get_state(account_id)
        state.kill_switch_active = active
        state.status = RiskMonitorStatus.KILL_SWITCH if active else RiskMonitorStatus.HEALTHY
        await self.save_state(state)

    async def reset_daily(self, account_id: UUID) -> AccountRiskState:
        state = await self.get_state(account_id)
        state.daily_pnl = Decimal("0")
        state.peak_equity = state.current_equity
        state.drawdown_usd = Decimal("0")
        state.last_reset_at = datetime.now(tz=UTC)
        state.status = RiskMonitorStatus.HEALTHY
        await self.save_state(state)
        logger.info("risk_daily_reset", account_id=str(account_id))
        return state

    async def publish_status(self, user_id: UUID, payload: dict[str, object]) -> None:
        channel = f"risk:status:{user_id}"
        await self._redis.publish(channel, json.dumps(payload))

    @staticmethod
    def _key(account_id: UUID) -> str:
        return f"risk:state:{account_id}"
