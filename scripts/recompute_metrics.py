#!/usr/bin/env python3
"""Hash-gate and replay metrics from a retained private holdout NPZ."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.verify import build_verification_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = build_verification_report(
        repository_root=ROOT,
        holdout_series=args.series,
    )
    private = report["private_evidence"]["holdout_series"]
    if args.as_json:
        print(json.dumps(private, indent=2, sort_keys=True))
    else:
        metrics = private["analysis"]
        print(f"PASS: {private['identity']['artifact_id']} verified before parsing")
        print(f"Total return: {metrics['total_return']:.12f}")
        print(f"Net Sharpe: {metrics['net_sharpe']:.12f}")
        print(f"Maximum drawdown: {metrics['max_drawdown']:.12f}")
        print(f"Calmar (elapsed calendar time): {metrics['calendar_calmar_ratio']:.12f}")
        print(f"Calmar (252-session convention): {metrics['calmar_ratio']:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
