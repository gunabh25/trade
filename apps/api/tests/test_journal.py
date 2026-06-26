"""Trading journal unit tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
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


def test_export_csv() -> None:
    from tradeflow.features.journal.export import export_entries_csv
    from tradeflow.features.journal.schemas import JournalEntryResponse

    entry = JournalEntryResponse(
        id=uuid4(),
        title="Test",
        content=None,
        notes=None,
        mood=None,
        session_date=date.today(),
        pnl=Decimal("100"),
        tags=["tag1"],
        emotions=["calm"],
        mistakes=["chased entry"],
        lessons_learned="Wait",
        source=JournalSource.MANUAL,
        symbol="ES",
        side=TradeSide.LONG,
        quantity=Decimal("1"),
        entry_price=Decimal("100"),
        exit_price=Decimal("101"),
        grade=4,
        trade_id=None,
        strategy_id=None,
        trading_account_id=None,
        strategy=None,
        screenshots=[],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    csv_bytes = export_entries_csv([entry])
    assert b"ES" in csv_bytes
    assert b"4" in csv_bytes


def test_grade_validation() -> None:
    req = CreateJournalEntryRequest(
        title="Graded trade",
        session_date=date.today(),
        grade=5,
    )
    assert req.grade == 5


def test_journal_source_enum() -> None:
    assert JournalSource.AUTO_IMPORT.value == "auto_import"
    assert JournalSource.MANUAL.value == "manual"
