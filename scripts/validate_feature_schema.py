#!/usr/bin/env python3
"""Validate headers of separately retained private feature CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.schema import SYMBOLS, validate_feature_csv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_directory", type=Path)
    args = parser.parse_args()
    for symbol in SYMBOLS:
        path = args.feature_directory / f"{symbol}.csv"
        columns = validate_feature_csv(path, symbol)
        print(f"PASS {symbol}: {len(columns)} frozen features")
    print("Schema validation does not by itself establish a full model rerun.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
