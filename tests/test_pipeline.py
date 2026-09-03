import numpy as np

from reservoir_market_backtest.model import IkedaConfiguration
from reservoir_market_backtest.pipeline import (
    equal_weight_common_dates,
    run_symbol_backtest,
)
from reservoir_market_backtest.volatility import (
    har_volatility_forecast,
    trailing_mean_with_initial_backfill,
)


def tiny_ikeda() -> IkedaConfiguration:
    return IkedaConfiguration(
        virtual_nodes=6,
        theta_steps=2,
        dt=0.05,
        feedback_gain_beta=0.3,
        phase_offset=0.8,
        input_scale=0.02,
        auxiliary_delta=0.0,
        desynchronization=1,
        mask_seed=1234,
    )


def test_trailing_mean_matches_historical_initial_backfill() -> None:
    values = np.arange(1.0, 7.0)
    actual = trailing_mean_with_initial_backfill(values, 3)
    np.testing.assert_allclose(actual, [2.0, 2.0, 2.0, 3.0, 4.0, 5.0])


def test_har_forecast_is_expanding_and_deterministic() -> None:
    n = 80
    sigma = 0.01 + np.arange(n) * 1e-5
    target = np.log(np.roll(sigma, -1))
    target[-1] = target[-2]
    first = har_volatility_forecast(
        sigma,
        target,
        initial_training_days=40,
        retrain_every=10,
        embargo=3,
    )
    second = har_volatility_forecast(
        sigma,
        target,
        initial_training_days=40,
        retrain_every=10,
        embargo=3,
    )
    np.testing.assert_array_equal(first.sigma, second.sigma)
    assert not first.fitted_rows[:40].any()
    assert first.fitted_rows[40:].all()
    np.testing.assert_allclose(first.sigma[:40], sigma[:40])


def test_complete_symbol_pipeline_returns_aligned_costed_path() -> None:
    rng = np.random.default_rng(9)
    n = 140
    features = rng.normal(size=(n, 4))
    next_returns = rng.normal(0.0002, 0.01, n)
    direction = np.where(next_returns >= 0.0, 1.0, -1.0)
    sigma = np.full(n, 0.01)
    next_log_sigma = np.log(sigma)
    result = run_symbol_backtest(
        features,
        direction,
        next_returns,
        sigma,
        next_log_sigma,
        walk_forward_start_index=100,
        har_initial_training_days=60,
        configuration=tiny_ikeda(),
    )
    assert result.reservoir_states.shape == (n, 6)
    assert result.evaluation_indices.tolist() == list(range(100, n))
    assert result.p_up.shape == (40,)
    assert result.strategy.net_returns.shape == (40,)
    assert np.isfinite(result.strategy.net_returns).all()


def test_reporting_slice_does_not_shift_walk_forward_refits() -> None:
    rng = np.random.default_rng(11)
    n = 150
    features = rng.normal(size=(n, 3))
    returns = rng.normal(0.0, 0.01, n)
    target = np.where(returns >= 0.0, 1.0, -1.0)
    sigma = np.full(n, 0.01)
    common = dict(
        features=features,
        direction_target=target,
        next_return=returns,
        current_sigma=sigma,
        next_log_sigma=np.log(sigma),
        walk_forward_start_index=70,
        har_initial_training_days=50,
        configuration=tiny_ikeda(),
    )
    development_and_holdout = run_symbol_backtest(**common)
    holdout_only = run_symbol_backtest(**common, result_start_index=113)
    selected = development_and_holdout.evaluation_indices >= 113
    np.testing.assert_array_equal(
        holdout_only.evaluation_indices,
        development_and_holdout.evaluation_indices[selected],
    )
    np.testing.assert_allclose(
        holdout_only.direction_scores,
        development_and_holdout.direction_scores[selected],
    )
    np.testing.assert_allclose(
        holdout_only.strategy.net_returns,
        development_and_holdout.strategy.net_returns[selected],
    )
    assert holdout_only.strategy.net_returns[0] == (
        development_and_holdout.strategy.net_returns[selected][0]
    )


def test_historical_feature_nan_rule_is_zero_fill() -> None:
    rng = np.random.default_rng(12)
    n = 100
    features = rng.normal(size=(n, 3))
    features[4, 1] = np.nan
    zero_filled = np.nan_to_num(features, nan=0.0)
    returns = rng.normal(0.0, 0.01, n)
    target = np.where(returns >= 0.0, 1.0, -1.0)
    sigma = np.full(n, 0.01)
    kwargs = dict(
        direction_target=target,
        next_return=returns,
        current_sigma=sigma,
        next_log_sigma=np.log(sigma),
        walk_forward_start_index=70,
        har_initial_training_days=50,
        configuration=tiny_ikeda(),
    )
    with_nan = run_symbol_backtest(features=features, **kwargs)
    explicit_zero = run_symbol_backtest(features=zero_filled, **kwargs)
    np.testing.assert_array_equal(
        with_nan.reservoir_states,
        explicit_zero.reservoir_states,
    )


def test_historical_direction_target_allows_zero_return_sign() -> None:
    rng = np.random.default_rng(13)
    n = 100
    features = rng.normal(size=(n, 3))
    returns = rng.normal(0.0, 0.01, n)
    returns[8] = 0.0
    target = np.sign(returns)
    sigma = np.full(n, 0.01)
    result = run_symbol_backtest(
        features,
        target,
        returns,
        sigma,
        np.log(sigma),
        walk_forward_start_index=70,
        har_initial_training_days=50,
        configuration=tiny_ikeda(),
    )
    assert result.evaluation_indices.size == 30


def test_equal_weight_portfolio_uses_only_common_dates() -> None:
    dates, returns = equal_weight_common_dates(
        {
            "A": (np.array([1, 2, 3]), np.array([0.01, 0.02, 0.03])),
            "B": (np.array([2, 3, 4]), np.array([-0.02, 0.04, 0.10])),
        }
    )
    np.testing.assert_array_equal(dates, [2, 3])
    np.testing.assert_allclose(returns, [0.0, 0.035])
