"""Clean implementation of the historical position and cost rule."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class StrategyResult:
    """Daily net returns, daily weights, and annualized one-way turnover."""

    net_returns: np.ndarray
    weights: np.ndarray
    annualized_turnover: float


def _finite_vector(name: str, values: Iterable[float] | np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    return array


def strategy_returns(
    p_up: Iterable[float] | np.ndarray,
    sigma_prediction: Iterable[float] | np.ndarray,
    next_return: Iterable[float] | np.ndarray,
    *,
    annual_volatility_target: float = 0.10,
    periods_per_year: int = 252,
    cost_bps: float = 2.5,
    maximum_absolute_weight: float = 1.0,
) -> StrategyResult:
    """Apply the exact historical confidence/volatility-scaled trading rule.

    ``confidence = 2 * (P(up) - 0.5)`` and
    ``weight = clip(confidence * daily_vol_target / sigma_prediction, +/- cap)``.
    Costs are charged on the absolute change in weight, including entry from a
    zero initial position. This function reconstructs methodology; it is not an
    investment recommendation or an execution simulator.
    """

    probabilities = _finite_vector("p_up", p_up)
    sigma = _finite_vector("sigma_prediction", sigma_prediction)
    returns = _finite_vector("next_return", next_return)
    if not (probabilities.size == sigma.size == returns.size):
        raise ValueError("p_up, sigma_prediction, and next_return must have equal length")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("p_up must lie in [0, 1]")
    if annual_volatility_target <= 0.0 or periods_per_year <= 0:
        raise ValueError("volatility target and periods_per_year must be positive")
    if cost_bps < 0.0 or maximum_absolute_weight <= 0.0:
        raise ValueError("cost_bps must be nonnegative and the weight cap positive")

    confidence = 2.0 * (probabilities - 0.5)
    daily_target = annual_volatility_target / math.sqrt(periods_per_year)
    weights = np.clip(
        confidence * daily_target / np.maximum(sigma, 1e-6),
        -maximum_absolute_weight,
        maximum_absolute_weight,
    )
    weight_change = np.abs(np.diff(np.concatenate(([0.0], weights))))
    costs = weight_change * cost_bps * 1e-4
    net_returns = weights * returns - costs
    years = max(weights.size / periods_per_year, 1e-9)
    return StrategyResult(
        net_returns=net_returns,
        weights=weights,
        annualized_turnover=float(weight_change.sum() / years),
    )
