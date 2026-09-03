#!/usr/bin/env python3
"""Regenerate the exact public-file allowlist after a release review."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reservoir_market_backtest.release_manifest import write_release_manifest  # noqa: E402


if __name__ == "__main__":
    destination = write_release_manifest(ROOT)
    print(f"Wrote {destination.relative_to(ROOT)}")
