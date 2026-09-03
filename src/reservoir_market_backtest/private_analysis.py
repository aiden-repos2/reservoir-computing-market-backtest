"""Analysis of optional hash-verified private NumPy evidence files."""

from __future__ import annotations

from pathlib import Path
from datetime import date
from typing import Any

import numpy as np

from .metrics import calendar_annual_growth_rate, summarize_returns
from .schema import SYMBOLS


class PrivateArtifactSchemaError(ValueError):
    """Raised when a verified private artifact has an unexpected array schema."""


def _require_keys(archive: Any, keys: set[str]) -> None:
    missing = sorted(keys - set(archive.files))
    if missing:
        raise PrivateArtifactSchemaError(f"private NPZ is missing arrays: {missing}")


def analyze_holdout_series(path: str | Path) -> dict[str, Any]:
    """Reconstruct the equal-weight Ikeda portfolio and its exact Calmar ratio."""

    with np.load(Path(path), allow_pickle=False) as archive:
        required = {
            item
            for symbol in SYMBOLS
            for item in (
                f"ikeda1__{symbol}__dt",
                f"ikeda1__{symbol}__ret",
            )
        }
        _require_keys(archive, required)
        dated_returns: dict[str, dict[int, float]] = {}
        common_dates: set[int] | None = None
        for symbol in SYMBOLS:
            dates = np.asarray(archive[f"ikeda1__{symbol}__dt"], dtype=np.int64)
            returns = np.asarray(archive[f"ikeda1__{symbol}__ret"], dtype=np.float64)
            if dates.ndim != 1 or returns.ndim != 1 or dates.size != returns.size:
                raise PrivateArtifactSchemaError(f"invalid holdout arrays for {symbol}")
            if dates.size != np.unique(dates).size:
                raise PrivateArtifactSchemaError(f"duplicate holdout dates for {symbol}")
            if not np.isfinite(returns).all():
                raise PrivateArtifactSchemaError(f"non-finite holdout returns for {symbol}")
            dated_returns[symbol] = dict(zip(dates.tolist(), returns.tolist(), strict=True))
            symbol_dates = set(int(value) for value in dates)
            common_dates = symbol_dates if common_dates is None else common_dates & symbol_dates

        ordered_dates = np.asarray(sorted(common_dates or ()), dtype=np.int64)
        if ordered_dates.size == 0:
            raise PrivateArtifactSchemaError("holdout series have no common dates")
        matrix = np.column_stack(
            [
                np.asarray([dated_returns[symbol][int(date)] for date in ordered_dates])
                for symbol in SYMBOLS
            ]
        )
        portfolio_returns = np.mean(matrix, axis=1)
        metrics = summarize_returns(portfolio_returns).to_dict()
        first_date = str(ordered_dates[0].astype("datetime64[ns]").astype("datetime64[D]"))
        last_date = str(ordered_dates[-1].astype("datetime64[ns]").astype("datetime64[D]"))
        calendar_cagr = calendar_annual_growth_rate(
            float(metrics["final_equity"]),
            date.fromisoformat(first_date),
            date.fromisoformat(last_date),
        )
        return {
            "symbols": list(SYMBOLS),
            "n_symbols": len(SYMBOLS),
            "first_date": first_date,
            "last_date": last_date,
            **metrics,
            "elapsed_calendar_days": (
                date.fromisoformat(last_date) - date.fromisoformat(first_date)
            ).days,
            "calendar_annualized_return_cagr": calendar_cagr,
            "calendar_calmar_ratio": float(calendar_cagr / abs(float(metrics["max_drawdown"]))),
        }

