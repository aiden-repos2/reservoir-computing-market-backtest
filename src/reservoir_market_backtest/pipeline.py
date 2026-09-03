"""End-to-end method reconstruction for supplied chronological feature arrays.

The public repository does not redistribute the historical market feature
rows. This module nevertheless makes the complete computational path explicit:
features -> simulated Ikeda states -> expanding ridge scores -> HAR volatility
sizing -> cost-adjusted strategy returns -> equal-weight portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .backtest import StrategyResult, strategy_returns
from .model import (
    FROZEN_IKEDA_CONFIGURATION,
    IkedaConfiguration,
    ikeda_states,
    scores_to_up_values,
    walk_forward_ridge_scores,
)
from .volatility import VolatilityForecast, har_volatility_forecast


@dataclass(frozen=True)
class SymbolBacktest:
    """Aligned outputs for the rows evaluated by the directional readout."""

    evaluation_indices: np.ndarray
    reservoir_states: np.ndarray
    direction_scores: np.ndarray
    p_up: np.ndarray
    volatility: VolatilityForecast
    strategy: StrategyResult


def run_symbol_backtest(
    features: np.ndarray,
    direction_target: np.ndarray,
    next_return: np.ndarray,
    current_sigma: np.ndarray,
    next_log_sigma: np.ndarray,
    *,
    walk_forward_start_index: int,
    result_start_index: int | None = None,
    configuration: IkedaConfiguration = FROZEN_IKEDA_CONFIGURATION,
    direction_penalty: float = 1.0,
    retrain_every: int = 21,
    embargo: int = 5,
    har_initial_training_days: int = 504,
    har_penalty: float = 1e-4,
) -> SymbolBacktest:
    """Run the historical simulated-reservoir strategy on supplied arrays.

    ``walk_forward_start_index`` anchors the first prediction/refit block. For
    the historical run this was the first 2016 row. Predictions, positions, and
    transaction costs are then computed as one continuous stream.
    ``result_start_index`` may select a later reporting interval without
    shifting the refit schedule or resetting the prior position; the historical
    holdout was selected at the first 2024 row. At each refit, the expanding
    training sample ends ``embargo`` sessions before the next block.

    The historical loader replaced missing feature values with zero. Infinite
    feature values and any nonfinite target, return, or volatility value are
    rejected.
    """

    matrix = np.asarray(features, dtype=np.float64)
    target = np.asarray(direction_target, dtype=np.float64).reshape(-1)
    returns = np.asarray(next_return, dtype=np.float64)
    sigma_now = np.asarray(current_sigma, dtype=np.float64)
    sigma_next = np.asarray(next_log_sigma, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("features must be a nonempty two-dimensional matrix")
    n_rows = matrix.shape[0]
    if any(array.ndim != 1 or array.size != n_rows for array in (
        target,
        returns,
        sigma_now,
        sigma_next,
    )):
        raise ValueError("every target, return, and volatility vector must align")
    if np.isinf(matrix).any():
        raise ValueError("features contain infinite values")
    matrix = np.nan_to_num(matrix, nan=0.0, copy=True)
    if not all(np.isfinite(array).all() for array in (
        target,
        returns,
        sigma_now,
        sigma_next,
    )):
        raise ValueError("pipeline inputs contain NaN or infinite values")
    if not np.isin(target, (-1.0, 0.0, 1.0)).all():
        raise ValueError("direction_target must use the historical sign encoding")

    states = ikeda_states(matrix, configuration)
    scores, evaluated = walk_forward_ridge_scores(
        states,
        target,
        initial_training_days=walk_forward_start_index,
        penalty=direction_penalty,
        retrain_every=retrain_every,
        embargo=embargo,
    )
    volatility = har_volatility_forecast(
        sigma_now,
        sigma_next,
        initial_training_days=har_initial_training_days,
        penalty=har_penalty,
        retrain_every=retrain_every,
        embargo=embargo,
    )
    reporting_start = (
        walk_forward_start_index if result_start_index is None else result_start_index
    )
    if not walk_forward_start_index <= reporting_start < n_rows:
        raise ValueError(
            "result_start_index must be no earlier than the walk-forward start "
            "and must lie inside the series"
        )
    evaluated_indices = np.flatnonzero(evaluated)
    all_direction_scores = scores[evaluated]
    all_p_up = scores_to_up_values(all_direction_scores)
    continuous_strategy = strategy_returns(
        all_p_up,
        volatility.sigma[evaluated],
        returns[evaluated],
    )
    report_on_evaluated = evaluated_indices >= reporting_start
    first_report_offset = int(np.flatnonzero(report_on_evaluated)[0])
    prior_weight = (
        0.0
        if first_report_offset == 0
        else float(continuous_strategy.weights[first_report_offset - 1])
    )
    report_weights = continuous_strategy.weights[report_on_evaluated]
    report_changes = np.abs(np.diff(np.concatenate(([prior_weight], report_weights))))
    report_years = max(report_weights.size / 252, 1e-9)
    strategy = StrategyResult(
        net_returns=continuous_strategy.net_returns[report_on_evaluated],
        weights=report_weights,
        annualized_turnover=float(report_changes.sum() / report_years),
    )
    indices = evaluated_indices[report_on_evaluated]
    direction_scores = all_direction_scores[report_on_evaluated]
    p_up = all_p_up[report_on_evaluated]
    return SymbolBacktest(
        evaluation_indices=indices,
        reservoir_states=states,
        direction_scores=direction_scores,
        p_up=p_up,
        volatility=volatility,
        strategy=strategy,
    )


def equal_weight_common_dates(
    dated_returns: Mapping[str, tuple[np.ndarray, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray]:
    """Equal-weight symbol returns on their exact intersection of dates."""

    if not dated_returns:
        raise ValueError("at least one symbol series is required")
    normalized: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    common: np.ndarray | None = None
    for symbol, (dates, returns) in dated_returns.items():
        date_array = np.asarray(dates)
        return_array = np.asarray(returns, dtype=np.float64)
        if date_array.ndim != 1 or return_array.ndim != 1 or date_array.size != return_array.size:
            raise ValueError(f"dates and returns are not aligned for {symbol}")
        if date_array.size == 0 or np.unique(date_array).size != date_array.size:
            raise ValueError(f"dates must be nonempty and unique for {symbol}")
        if not np.isfinite(return_array).all():
            raise ValueError(f"returns contain NaN or infinite values for {symbol}")
        order = np.argsort(date_array)
        date_array = date_array[order]
        return_array = return_array[order]
        normalized[symbol] = (date_array, return_array)
        common = date_array if common is None else np.intersect1d(common, date_array)
    if common is None or common.size == 0:
        raise ValueError("symbol series have no common dates")
    columns = []
    for symbol, (dates, returns) in normalized.items():
        positions = np.searchsorted(dates, common)
        if not np.array_equal(dates[positions], common):
            raise RuntimeError(f"common-date alignment failed for {symbol}")
        columns.append(returns[positions])
    return common, np.mean(np.column_stack(columns), axis=1)
