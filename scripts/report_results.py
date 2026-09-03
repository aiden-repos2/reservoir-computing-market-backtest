#!/usr/bin/env python3
"""Print the immutable historical holdout aggregate."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.reference import load_json, validate_reference  # noqa: E402


def main() -> int:
    reference = load_json(ROOT / "results" / "reference_results.json")
    validate_reference(reference)
    holdout = reference["historical_holdout"]
    metrics = holdout["portfolio_metrics"]
    print("Historical simulated holdout")
    print(f"  Dates: {holdout['first_date']} through {holdout['last_date']}")
    print(f"  Total return: {metrics['total_return']:.4%}")
    print(f"  Net Sharpe: {metrics['net_sharpe']:.4f}")
    print(f"  Maximum drawdown: {metrics['max_drawdown']:.4%}")
    print(f"  Calmar (elapsed calendar time): {metrics['calendar_calmar_ratio']:.4f}")
    print(f"  Calmar (252-session convention): {metrics['session_calmar_ratio']:.4f}")
    print(f"  Mean per-symbol raw accuracy: {holdout['mean_per_symbol_raw_accuracy']:.4%}")
    print("  Scope: retrospective simulated result; no prospective-performance claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
