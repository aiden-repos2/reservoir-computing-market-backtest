import math

import numpy as np
import pytest

from reservoir_market_backtest.backtest import strategy_returns


def test_historical_position_and_cost_rule() -> None:
    p_up = np.array([0.60, 0.40])
    sigma = np.array([0.01, 0.01])
    next_return = np.array([0.01, -0.02])
    result = strategy_returns(p_up, sigma, next_return)

    size = 0.20 * (0.10 / math.sqrt(252)) / 0.01
    expected_weights = np.array([size, -size])
    expected_changes = np.array([size, 2 * size])
    expected_net = expected_weights * next_return - expected_changes * 2.5e-4
    np.testing.assert_allclose(result.weights, expected_weights)
    np.testing.assert_allclose(result.net_returns, expected_net)
    assert result.annualized_turnover == pytest.approx(expected_changes.sum() / (2 / 252))


def test_position_cap_and_probability_validation() -> None:
    result = strategy_returns([1.0], [1e-9], [0.01])
    assert result.weights.tolist() == [1.0]
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        strategy_returns([1.1], [0.01], [0.01])
