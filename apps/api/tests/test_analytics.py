"""Enterprise analytics unit tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from tradeflow.features.analytics import metrics


def test_win_rate_and_profit_factor() -> None:
    pnls = [Decimal("100"), Decimal("200"), Decimal("-50")]
    result = metrics.compute_trade_metrics(pnls)
    assert result["win_count"] == 2
    assert result["loss_count"] == 1
    assert round(result["win_rate"], 2) == 66.67
    assert result["profit_factor"] == 6.0


def test_expectancy_and_average_r() -> None:
    pnls = [Decimal("200"), Decimal("-100"), Decimal("100")]
    assert metrics.expectancy(pnls) == 200 / 3
    avg_r = metrics.average_r(pnls)
    assert avg_r is not None
    assert round(avg_r, 2) == round((2 + -1 + 1) / 3, 2)


def test_sharpe_and_sortino() -> None:
    returns = [0.01, 0.005, -0.002, 0.008, 0.003, -0.001, 0.004]
    sharpe = metrics.sharpe_ratio(returns)
    sortino = metrics.sortino_ratio(returns)
    assert sharpe is not None
    assert sortino is not None
    assert sortino > sharpe


def test_equity_curve_and_drawdown() -> None:
    daily = [
        (date(2026, 1, 1), Decimal("1000")),
        (date(2026, 1, 2), Decimal("-500")),
        (date(2026, 1, 3), Decimal("200")),
    ]
    curve = metrics.equity_curve_from_daily(daily, Decimal("100000"))
    assert curve[0][1] == 101000.0
    assert curve[1][1] == 100500.0

    dd = metrics.drawdown_series(curve)
    assert dd[0][1] == 0.0
    assert dd[1][1] < 0


def test_aggregate_daily_pnls() -> None:
    rows = [
        (date(2026, 1, 1), Decimal("100")),
        (date(2026, 1, 1), Decimal("50")),
        (date(2026, 1, 2), Decimal("-30")),
    ]
    aggregated = metrics.aggregate_daily_pnls(rows)
    assert len(aggregated) == 2
    assert aggregated[0][1] == Decimal("150")
