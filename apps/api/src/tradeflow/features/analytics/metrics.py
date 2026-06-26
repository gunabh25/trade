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


def loss_rate(losses: int, total: int) -> float:
    if total == 0:
        return 0.0
    return losses / total * 100


def average_win(pnls: list[Decimal]) -> float:
    wins = [_to_float(p) for p in pnls if p > 0]
    if not wins:
        return 0.0
    return sum(wins) / len(wins)


def average_loss(pnls: list[Decimal]) -> float:
    losses = [abs(_to_float(p)) for p in pnls if p < 0]
    if not losses:
        return 0.0
    return sum(losses) / len(losses)


def recovery_factor(net_profit: float, max_drawdown_dollars: float) -> float | None:
    if max_drawdown_dollars == 0:
        return None
    return net_profit / abs(max_drawdown_dollars)


def max_consecutive_streaks(pnls: list[Decimal]) -> tuple[int, int]:
    max_wins = max_losses = current_wins = current_losses = 0
    for pnl in pnls:
        if pnl > 0:
            current_wins += 1
            current_losses = 0
            max_wins = max(max_wins, current_wins)
        elif pnl < 0:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0
    return max_wins, max_losses


def max_drawdown_dollars(equity_points: list[tuple[date, float]]) -> float:
    peak = 0.0
    max_dd = 0.0
    for _, equity in equity_points:
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return max_dd


def profit_curve_from_trades(
    trade_pnls: list[tuple[date, Decimal]],
) -> list[tuple[int, float]]:
    """Cumulative P&L curve indexed by trade number (1-based)."""
    cumulative = 0.0
    curve: list[tuple[int, float]] = []
    for index, (_, pnl) in enumerate(sorted(trade_pnls, key=lambda x: x[0]), start=1):
        cumulative += _to_float(pnl)
        curve.append((index, cumulative))
    return curve


def trade_distribution(
    pnls: list[Decimal],
    *,
    bucket_count: int = 8,
) -> list[tuple[str, int]]:
    """Histogram buckets for per-trade P&L distribution."""
    if not pnls:
        return []

    values = [_to_float(p) for p in pnls]
    min_val = min(values)
    max_val = max(values)
    if min_val == max_val:
        return [(f"${min_val:,.0f}", len(values))]

    span = max_val - min_val
    step = span / bucket_count
    buckets = [0] * bucket_count
    for value in values:
        idx = min(int((value - min_val) / step), bucket_count - 1) if step > 0 else 0
        buckets[idx] += 1

    labels: list[tuple[str, int]] = []
    for i, count in enumerate(buckets):
        low = min_val + step * i
        high = min_val + step * (i + 1)
        label = f"${low:,.0f}-${high:,.0f}"
        labels.append((label, count))
    return labels


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
            "loss_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": None,
            "expectancy": 0.0,
            "average_r": None,
            "total_pnl": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
        }

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    breakeven = [p for p in pnls if p == 0]
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    max_wins, max_losses = max_consecutive_streaks(pnls)

    return {
        "win_count": len(wins),
        "loss_count": len(losses),
        "breakeven_count": len(breakeven),
        "win_rate": win_rate(len(wins), len(pnls)),
        "loss_rate": loss_rate(len(losses), len(pnls)),
        "avg_win": average_win(pnls),
        "avg_loss": average_loss(pnls),
        "profit_factor": profit_factor(gross_profit, gross_loss),
        "expectancy": expectancy(pnls),
        "average_r": average_r(pnls),
        "total_pnl": _to_float(sum(pnls, Decimal("0"))),
        "max_consecutive_wins": max_wins,
        "max_consecutive_losses": max_losses,
    }
