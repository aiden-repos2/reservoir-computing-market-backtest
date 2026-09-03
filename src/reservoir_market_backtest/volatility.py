"""Causal HAR-style volatility forecast used for historical position sizing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import walk_forward_ridge_scores


@dataclass(frozen=True)
class VolatilityForecast:
    """Daily volatility estimate and the rows produced by fitted HAR readouts."""

    sigma: np.ndarray
    log_sigma: np.ndarray
    fitted_rows: np.ndarray


def trailing_mean_with_initial_backfill(values: np.ndarray, window: int) -> np.ndarray:
    """Match the historical ``rolling(window).mean().bfill()`` construction."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("values must be a nonempty one-dimensional array")
    if not np.isfinite(array).all():
        raise ValueError("values contain NaN or infinite values")
    if not 1 <= window <= array.size:
        raise ValueError("window must lie between one and the series length")
    cumulative = np.concatenate(([0.0], np.cumsum(array)))
    complete = (cumulative[window:] - cumulative[:-window]) / window
    result = np.empty_like(array)
    result[window - 1 :] = complete
    result[: window - 1] = complete[0]
    return result


def har_volatility_forecast(
    current_sigma: np.ndarray,
    next_log_sigma: np.ndarray,
    *,
    initial_training_days: int = 504,
    penalty: float = 1e-4,
    retrain_every: int = 21,
    embargo: int = 5,
) -> VolatilityForecast:
    """Reconstruct the expanding HAR sizing leg of the historical pipeline.

    The three regressors are current log volatility and its trailing 5- and
    21-session means. Before the first 504-session fit, the historical code
    used current log volatility as a random-walk fallback.
    """

    sigma = np.asarray(current_sigma, dtype=np.float64)
    target = np.asarray(next_log_sigma, dtype=np.float64)
    if sigma.ndim != 1 or target.ndim != 1 or sigma.shape != target.shape:
        raise ValueError("current_sigma and next_log_sigma must be aligned vectors")
    if sigma.size == 0 or not np.isfinite(sigma).all() or not np.isfinite(target).all():
        raise ValueError("volatility inputs must be nonempty and finite")

    log_sigma_now = np.log(np.clip(sigma, 1e-8, None))
    design = np.column_stack(
        (
            log_sigma_now,
            trailing_mean_with_initial_backfill(log_sigma_now, 5),
            trailing_mean_with_initial_backfill(log_sigma_now, 21),
        )
    )
    fitted_log_sigma, fitted_rows = walk_forward_ridge_scores(
        design,
        target,
        initial_training_days=initial_training_days,
        penalty=penalty,
        retrain_every=retrain_every,
        embargo=embargo,
    )
    log_forecast = np.where(fitted_rows, fitted_log_sigma, log_sigma_now)
    forecast = np.exp(log_forecast)
    if not np.isfinite(forecast).all() or np.any(forecast <= 0.0):
        raise FloatingPointError("HAR volatility forecast is not finite and positive")
    return VolatilityForecast(forecast, log_forecast, fitted_rows)
