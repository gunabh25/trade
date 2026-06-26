"""Pure analytics metric calculations."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from decimal import Decimal


def _to_float(value: Decimal | float | int) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def win_rate(wins: int, total: int) -> float:
    if total == 0:
        return 0.0
    return wins / total * 100


def profit_factor(gross_profit: Decimal, gross_loss: Decimal) -> float | None:
    loss = abs(_to_float(gross_loss))
    if loss == 0:
        return None
    return _to_float(gross_profit) / loss


def expectancy(pnls: list[Decimal]) -> float:
    if not pnls:
        return 0.0
    return sum(_to_float(p) for p in pnls) / len(pnls)


def average_r(pnls: list[Decimal]) -> float | None:
    """R-multiple using average loss as 1R when explicit risk is unavailable."""
    losses = [abs(_to_float(p)) for p in pnls if p < 0]
    if not losses or not pnls:
        return None
    one_r = sum(losses) / len(losses)
    if one_r == 0:
        return None
    return sum(_to_float(p) / one_r for p in pnls) / len(pnls)


def sharpe_ratio(
    daily_returns: list[float],
    *,
    risk_free: float = 0.0,
    periods: int = 252,
) -> float | None:
    if len(daily_returns) < 2:
        return None
    mean = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return None
    return (mean - risk_free) * math.sqrt(periods) / std


def sortino_ratio(
    daily_returns: list[float],
    *,
    risk_free: float = 0.0,
    periods: int = 252,
) -> float | None:
    if len(daily_returns) < 2:
        return None
    mean = sum(daily_returns) / len(daily_returns)
    downside = [min(0.0, r - risk_free) for r in daily_returns]
    downside_variance = sum(d**2 for d in downside) / len(daily_returns)
    downside_std = math.sqrt(downside_variance)
    if downside_std == 0:
        return None
    return (mean - risk_free) * math.sqrt(periods) / downside_std


def equity_curve_from_daily(
    daily_pnls: list[tuple[date, Decimal]],
    starting_equity: Decimal,
) -> list[tuple[date, float]]:
    equity = _to_float(starting_equity)
    curve: list[tuple[date, float]] = []
    for day, pnl in sorted(daily_pnls, key=lambda x: x[0]):
        equity += _to_float(pnl)
        curve.append((day, equity))
    return curve


def drawdown_series(equity_points: list[tuple[date, float]]) -> list[tuple[date, float]]:
    peak = 0.0
    series: list[tuple[date, float]] = []
    for day, equity in equity_points:
        peak = max(peak, equity)
        dd = ((equity - peak) / peak * 100) if peak > 0 else 0.0
        series.append((day, dd))
    return series


def aggregate_daily_pnls(
    trade_pnls: list[tuple[date, Decimal]],
) -> list[tuple[date, Decimal]]:
    buckets: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    for day, pnl in trade_pnls:
        buckets[day] += pnl
    return sorted(buckets.items(), key=lambda x: x[0])


def daily_return_rates(
    daily_pnls: list[tuple[date, Decimal]],
    starting_equity: Decimal,
) -> list[float]:
    equity = _to_float(starting_equity)
    rates: list[float] = []
    for _, pnl in sorted(daily_pnls, key=lambda x: x[0]):
        if equity <= 0:
            rates.append(0.0)
        else:
            rates.append(_to_float(pnl) / equity)
        equity += _to_float(pnl)
    return rates


def monthly_returns(daily_pnls: list[tuple[date, Decimal]]) -> list[tuple[str, float]]:
    buckets: dict[str, float] = defaultdict(float)
    for day, pnl in daily_pnls:
        key = day.strftime("%Y-%m")
        buckets[key] += _to_float(pnl)
    return sorted((k, v) for k, v in buckets.items())


def compute_trade_metrics(pnls: list[Decimal]) -> dict[str, float | int | None]:
    if not pnls:
        return {
            "win_count": 0,
            "loss_count": 0,
            "breakeven_count": 0,
            "win_rate": 0.0,
            "profit_factor": None,
            "expectancy": 0.0,
            "average_r": None,
            "total_pnl": 0.0,
        }

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    breakeven = [p for p in pnls if p == 0]
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))

    return {
        "win_count": len(wins),
        "loss_count": len(losses),
        "breakeven_count": len(breakeven),
        "win_rate": win_rate(len(wins), len(pnls)),
        "profit_factor": profit_factor(gross_profit, gross_loss),
        "expectancy": expectancy(pnls),
        "average_r": average_r(pnls),
        "total_pnl": _to_float(sum(pnls, Decimal("0"))),
    }
