#!/usr/bin/env python3
"""Run the reconstructed method on deterministic synthetic data only."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.metrics import summarize_returns  # noqa: E402
from reservoir_market_backtest.model import IkedaConfiguration  # noqa: E402
from reservoir_market_backtest.pipeline import run_symbol_backtest  # noqa: E402


def main() -> int:
    rng = np.random.default_rng(2026)
    n = 700
    time = np.arange(n, dtype=float)
    features = np.column_stack(
        (
            np.sin(time / 9.0),
            np.cos(time / 17.0),
            rng.normal(0.0, 0.2, n),
            np.sin(time / 31.0) + rng.normal(0.0, 0.05, n),
        )
    )
    synthetic_returns = 0.002 * np.sin((time + 1.0) / 9.0) + rng.normal(0.0, 0.01, n)
    target = np.where(synthetic_returns >= 0.0, 1.0, -1.0)
    configuration = IkedaConfiguration(
        virtual_nodes=12,
        theta_steps=3,
        dt=0.05,
        feedback_gain_beta=0.3,
        phase_offset=0.8,
        input_scale=0.02,
        auxiliary_delta=0.0,
        desynchronization=2,
        mask_seed=1234,
    )
    current_sigma = np.full(n, 0.01)
    next_log_sigma = np.log(current_sigma)
    backtest = run_symbol_backtest(
        features,
        target,
        synthetic_returns,
        current_sigma,
        next_log_sigma,
        walk_forward_start_index=600,
        configuration=configuration,
    )
    metrics = summarize_returns(backtest.strategy.net_returns)
    print("Synthetic demonstration only — not historical market evidence")
    print(f"State matrix: {backtest.reservoir_states.shape}")
    print(f"Evaluated synthetic rows: {backtest.evaluation_indices.size}")
    print(f"Synthetic net Sharpe: {metrics.net_sharpe:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
