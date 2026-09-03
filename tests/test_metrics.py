from datetime import date
import math

import numpy as np
import pytest

from reservoir_market_backtest.metrics import (
    calendar_annual_growth_rate,
    maximum_drawdown,
    summarize_returns,
)


def test_maximum_drawdown_includes_initial_equity() -> None:
    # If initial equity were omitted, the first value (0.90) would incorrectly
    # become the running peak and this drawdown would be reported as zero.
    assert maximum_drawdown(np.array([-0.10, 0.20])) == pytest.approx(-0.10)


def test_summary_uses_compounding_sample_std_and_252_sessions() -> None:
    returns = np.array([0.01, -0.02, 0.03, 0.00])
    result = summarize_returns(returns)
    equity = np.prod(1.0 + returns)
    expected_drawdown = -0.02
    assert result.n_days == 4
    assert result.final_equity == pytest.approx(equity)
    assert result.total_return == pytest.approx(equity - 1.0)
    assert result.annualized_return_cagr == pytest.approx(equity ** (252 / 4) - 1.0)
    assert result.annualized_return_arithmetic == pytest.approx(returns.mean() * 252)
    assert result.annualized_volatility == pytest.approx(returns.std(ddof=1) * math.sqrt(252))
    assert result.net_sharpe == pytest.approx(
        returns.mean() / returns.std(ddof=1) * math.sqrt(252)
    )
    assert result.max_drawdown == pytest.approx(expected_drawdown)
    assert result.calmar_ratio == pytest.approx(
        result.annualized_return_cagr / abs(result.max_drawdown)
    )


def test_calendar_time_convention_is_explicit() -> None:
    actual = calendar_annual_growth_rate(
        1.057198913169459,
        date(2024, 1, 2),
        date(2026, 7, 6),
    )
    assert actual == pytest.approx(0.02242664205292355, abs=1e-14)


@pytest.mark.parametrize("values", [[], [0.0, np.nan], [[0.1], [0.2]], [-1.0, 0.1]])
def test_invalid_return_streams_fail_closed(values: object) -> None:
    with pytest.raises(ValueError):
        summarize_returns(values)  # type: ignore[arg-type]
