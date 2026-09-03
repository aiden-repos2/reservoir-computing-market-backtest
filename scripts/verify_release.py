#!/usr/bin/env python3
"""Run public-safe verification, with optional private evidence replay."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--repository-root", str(ROOT), *sys.argv[1:]]))
