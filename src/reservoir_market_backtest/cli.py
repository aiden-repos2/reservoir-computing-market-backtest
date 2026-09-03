"""Command-line interface for the historical backtest verifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .verify import build_verification_report, format_verification_report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Verify public aggregate claims and optional private evidence."
    )
    result.add_argument("--repository-root", type=Path)
    result.add_argument("--holdout-series", type=Path)
    result.add_argument("--json", action="store_true", dest="as_json")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report = build_verification_report(
        repository_root=args.repository_root,
        holdout_series=args.holdout_series,
    )
    print(
        json.dumps(report, indent=2, sort_keys=True)
        if args.as_json
        else format_verification_report(report)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
