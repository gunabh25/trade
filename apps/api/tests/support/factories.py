"""Test data factories — lightweight builders for domain objects."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from uuid import UUID, uuid4

from tradeflow.db.enums import (
    CopyGroupMode,
    CopyGroupStatus,
    CopyMode,
    OrderSide,
    OrderStatus,
    OrderType,
)
from tradeflow.db.models.copy_trading import CopyGroup, CopyGroupFollower
from tradeflow.db.models.trading import Order
from tradeflow.engine.types import FollowerContext, LeaderEvent, LeaderEventType
from tradeflow.features.auth.schemas import LoginRequest, RegisterRequest
from tradeflow.risk.types import AccountRiskState, ProposedOrder


def unique_email(prefix: str = "user") -> str:
    # example.com is RFC 2606 — accepted by EmailStr; .test is rejected as special-use
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def register_payload(
    *,
    email: str | None = None,
    password: str = "SecurePass1",
    first_name: str = "Test",
) -> dict[str, str]:
    return {
        "email": email or unique_email(),
        "password": password,
        "first_name": first_name,
    }


def register_request(**kwargs: object) -> RegisterRequest:
    data = register_payload()
    data.update({k: v for k, v in kwargs.items() if v is not None})
    return RegisterRequest(**data)  # type: ignore[arg-type]


def login_request(email: str, password: str = "SecurePass1") -> LoginRequest:
    return LoginRequest(email=email, password=password)


def leader_event(
    *,
    symbol: str = "ES",
    quantity: int = 2,
    side: OrderSide = OrderSide.BUY,
    copy_group_id: UUID | None = None,
) -> LeaderEvent:
    return LeaderEvent(
        id=f"evt-{uuid4().hex[:8]}",
        copy_group_id=copy_group_id or uuid4(),
        leader_account_id=uuid4(),
        user_id=uuid4(),
        event_type=LeaderEventType.ORDER_SUBMITTED,
        leader_order_id=f"ord-{uuid4().hex[:8]}",
        symbol=symbol,
        side=side,
        order_type=OrderType.MARKET,
        quantity=quantity,
    )


def follower_context(
    *,
    copy_mode: CopyMode = CopyMode.FIXED_QUANTITY,
    sizing_value: Decimal = Decimal("1"),
    enabled: bool = True,
) -> FollowerContext:
    return FollowerContext(
        follower_account_id=uuid4(),
        broker_connection_id=uuid4(),
        external_account_id="acct-test",
        copy_mode=copy_mode,
        sizing_value=sizing_value,
        enabled=enabled,
        status="active",
    )


def copy_group(**kwargs: object) -> CopyGroup:
    group = CopyGroup(
        id=uuid4(),
        user_id=uuid4(),
        leader_account_id=uuid4(),
        name="Test Group",
        mode=CopyGroupMode.LIVE,
        status=CopyGroupStatus.ACTIVE,
    )
    for key, value in kwargs.items():
        setattr(group, key, value)
    return group


def copy_group_follower(**kwargs: object) -> CopyGroupFollower:
    follower = CopyGroupFollower(
        id=uuid4(),
        copy_group_id=uuid4(),
        follower_account_id=uuid4(),
        enabled=True,
        copy_mode=CopyMode.FIXED_QUANTITY,
        sizing_value=Decimal("1"),
    )
    for key, value in kwargs.items():
        setattr(follower, key, value)
    return follower


def trading_order(**kwargs: object) -> Order:
    order = Order(
        id=uuid4(),
        user_id=uuid4(),
        trading_account_id=uuid4(),
        symbol="ES",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1,
        filled_quantity=0,
        status=OrderStatus.PENDING,
    )
    for key, value in kwargs.items():
        setattr(order, key, value)
    return order


def proposed_order(**kwargs: object) -> ProposedOrder:
    order = ProposedOrder(
        symbol="ES",
        side=OrderSide.BUY,
        quantity=1,
    )
    if kwargs:
        order = replace(order, **kwargs)  # type: ignore[arg-type]
    return order


def account_risk_state(**kwargs: object) -> AccountRiskState:
    state = AccountRiskState(trading_account_id=uuid4())
    for key, value in kwargs.items():
        setattr(state, key, value)
    return state
