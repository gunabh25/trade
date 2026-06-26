"""Trading journal unit tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from tradeflow.db.enums import JournalSource, TradeSide
from tradeflow.features.journal.schemas import CreateJournalEntryRequest, JournalFilterParams


def test_journal_stats_calculation() -> None:
    from tradeflow.db.models.journal import TradeJournal

    entries = [
        TradeJournal(user_id=uuid4(), title="W1", session_date=date.today(), pnl=Decimal("100")),
        TradeJournal(user_id=uuid4(), title="W2", session_date=date.today(), pnl=Decimal("200")),
        TradeJournal(user_id=uuid4(), title="L1", session_date=date.today(), pnl=Decimal("-50")),
    ]

    pnls = [e.pnl for e in entries if e.pnl is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))

    assert len(wins) == 2
    assert len(losses) == 1
    assert gross_profit / gross_loss == Decimal("6")


def test_create_entry_request_validation() -> None:
    req = CreateJournalEntryRequest(
        title="ES Long Breakout",
        session_date=date.today(),
        symbol="ES",
        side=TradeSide.LONG,
        quantity=2,
        pnl=Decimal("350"),
        tags=["breakout", "morning"],
        emotions=["confident", "disciplined"],
        mistakes=["entered early"],
        lessons_learned="Wait for confirmation candle",
    )
    assert req.title == "ES Long Breakout"
    assert len(req.tags or []) == 2


def test_filter_params_defaults() -> None:
    params = JournalFilterParams()
    assert params.page == 1
    assert params.page_size == 20


def test_journal_source_enum() -> None:
    assert JournalSource.AUTO_IMPORT.value == "auto_import"
    assert JournalSource.MANUAL.value == "manual"
