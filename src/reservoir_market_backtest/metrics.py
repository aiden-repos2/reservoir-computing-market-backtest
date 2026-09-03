"""Financial metrics used by the frozen historical backtest.

Two Calmar conventions are reported for the dated historical series. The
primary descriptive value annualizes by elapsed calendar time; the companion
session value annualizes at 252 sessions per year. ``calmar_ratio`` and
``summarize_returns`` implement the latter, while
``calendar_annual_growth_rate`` supplies the numerator for the former. Both use
the absolute peak-to-trough drawdown of the compounded daily equity curve.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import math
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PerformanceMetrics:
    """Summary of one chronological daily return stream."""

    n_days: int
    final_equity: float
    total_return: float
    annualized_return_cagr: float
    annualized_return_arithmetic: float
    annualized_volatility: float
    net_sharpe: float
    max_drawdown: float
    calmar_ratio: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def _returns_1d(returns: Iterable[float] | np.ndarray) -> np.ndarray:
    values = np.asarray(returns, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"returns must be one-dimensional, got shape {values.shape}")
    if values.size == 0:
        raise ValueError("returns must not be empty")
    if not np.isfinite(values).all():
        raise ValueError("returns contain NaN or infinite values")
    if np.any(values <= -1.0):
        raise ValueError("a simple return at or below -100% cannot be compounded")
    return values


def equity_curve(returns: Iterable[float] | np.ndarray) -> np.ndarray:
    """Return a unit-start compounded equity curve."""

    return np.cumprod(1.0 + _returns_1d(returns))


def maximum_drawdown(returns: Iterable[float] | np.ndarray) -> float:
    """Return the most negative peak-to-trough drawdown."""

    # Include initial equity. Without this, a loss on the first observation is
    # incorrectly treated as a new peak and its drawdown disappears.
    equity = np.concatenate(([1.0], equity_curve(returns)))
    running_peak = np.maximum.accumulate(equity)
    return float(np.min(equity / running_peak - 1.0))


def compound_annual_growth_rate(
    returns: Iterable[float] | np.ndarray,
    periods_per_year: int = 252,
) -> float:
    values = _returns_1d(returns)
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    final_equity = float(np.prod(1.0 + values))
    return float(final_equity ** (periods_per_year / values.size) - 1.0)


def sharpe_ratio(
    returns: Iterable[float] | np.ndarray,
    periods_per_year: int = 252,
) -> float:
    """Annualized zero-risk-free-rate Sharpe using sample standard deviation."""

    values = _returns_1d(returns)
    if values.size < 2:
        raise ValueError("at least two returns are required for a Sharpe ratio")
    sample_std = float(np.std(values, ddof=1))
    if sample_std == 0.0:
        return math.inf if float(np.mean(values)) > 0.0 else math.nan
    return float(np.mean(values) / sample_std * math.sqrt(periods_per_year))


def calmar_ratio(
    returns: Iterable[float] | np.ndarray,
    periods_per_year: int = 252,
) -> float:
    """CAGR divided by absolute maximum drawdown."""

    values = _returns_1d(returns)
    cagr = compound_annual_growth_rate(values, periods_per_year)
    drawdown = maximum_drawdown(values)
    if drawdown == 0.0:
        return math.inf if cagr > 0.0 else math.nan
    return float(cagr / abs(drawdown))


def calendar_annual_growth_rate(
    final_equity: float,
    first_date: date,
    last_date: date,
    *,
    days_per_year: float = 365.2425,
) -> float:
    """Annualize final equity over elapsed calendar days.

    The historical calculation uses the difference between the first and last dated
    sessions (916 days), with the mean Gregorian year of 365.2425 days.
    """

    elapsed_days = (last_date - first_date).days
    if final_equity <= 0.0:
        raise ValueError("final_equity must be positive")
    if elapsed_days <= 0 or days_per_year <= 0.0:
        raise ValueError("the date interval and days_per_year must be positive")
    return float(final_equity ** (days_per_year / elapsed_days) - 1.0)


def summarize_returns(
    returns: Iterable[float] | np.ndarray,
    periods_per_year: int = 252,
) -> PerformanceMetrics:
    """Compute all reported portfolio statistics from chronological returns."""

    values = _returns_1d(returns)
    equity = equity_curve(values)
    total_return = float(equity[-1] - 1.0)
    cagr = float(equity[-1] ** (periods_per_year / values.size) - 1.0)
    max_dd = maximum_drawdown(values)
    annualized_volatility = float(np.std(values, ddof=1) * math.sqrt(periods_per_year))
    return PerformanceMetrics(
        n_days=int(values.size),
        final_equity=float(equity[-1]),
        total_return=total_return,
        annualized_return_cagr=cagr,
        annualized_return_arithmetic=float(np.mean(values) * periods_per_year),
        annualized_volatility=annualized_volatility,
        net_sharpe=sharpe_ratio(values, periods_per_year),
        max_drawdown=max_dd,
        calmar_ratio=float(cagr / abs(max_dd)) if max_dd != 0.0 else math.inf,
    )
