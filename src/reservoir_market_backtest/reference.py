"""Validation and comparison of the public aggregate reference records."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .schema import SYMBOLS, base_feature_columns


class ReferenceValidationError(ValueError):
    """Raised when a public aggregate record violates its own contract."""


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ReferenceValidationError(f"expected a JSON object: {path}")
    return value


def _close(actual: float, expected: float, label: str, tolerance: float = 5e-13) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance):
        raise ReferenceValidationError(
            f"{label} mismatch: expected {expected!r}, got {actual!r}"
        )


def validate_reference(reference: dict[str, Any]) -> list[str]:
    """Fail closed if the aggregate reference is internally inconsistent."""

    if reference.get("schema_version") != "1.0.0":
        raise ReferenceValidationError("unsupported reference schema")
    identity = reference["study_identity"]
    if tuple(identity["symbols"]) != SYMBOLS:
        raise ReferenceValidationError("symbol order differs from the frozen contract")
    provenance = reference["dataset_provenance"]
    contract = provenance["historical_input_contract"]
    if contract["spy_feature_count"] != len(base_feature_columns("SPY")):
        raise ReferenceValidationError("SPY feature count is inconsistent")
    if contract["other_symbol_feature_count"] != len(base_feature_columns("QQQ")):
        raise ReferenceValidationError("non-SPY feature count is inconsistent")
    if provenance.get("private_rows_redistributed"):
        raise ReferenceValidationError("public reference must not claim private rows are shipped")
    if provenance.get("fresh_data_to_result_reproduction_claimed"):
        raise ReferenceValidationError("this package does not support a fresh full rerun")
    if contract.get("target_encoding") != (
        "y_dir = sign(next-session log adjusted-close return), in {-1, 0, +1}"
    ):
        raise ReferenceValidationError("direction-target encoding changed")
    if contract.get("missing_feature_policy") != (
        "replace missing model-input values with 0.0"
    ):
        raise ReferenceValidationError("historical missing-feature policy changed")

    method = reference["frozen_method"]
    if method["readout"].get("walk_forward_anchor") != (
        "first row on or after 2016-01-01"
    ):
        raise ReferenceValidationError("walk-forward anchor changed")
    if "after continuous scoring" not in method["readout"].get(
        "holdout_selection", ""
    ):
        raise ReferenceValidationError("holdout selection no longer preserves the score stream")
    if "does not reset the prior weight" not in method["portfolio"].get(
        "position_and_cost_stream", ""
    ):
        raise ReferenceValidationError("holdout transaction-cost boundary changed")

    holdout = reference["historical_holdout"]
    metrics = holdout["portfolio_metrics"]
    if holdout["n_days"] != 628 or holdout["n_symbols"] != len(SYMBOLS):
        raise ReferenceValidationError("holdout geometry changed")
    if holdout["symbol_days"] != holdout["n_days"] * holdout["n_symbols"]:
        raise ReferenceValidationError("holdout symbol-day count is inconsistent")
    _close(metrics["total_return"], metrics["final_equity"] - 1.0, "total return")
    expected_session_cagr = metrics["final_equity"] ** (252 / holdout["n_days"]) - 1.0
    _close(
        metrics["session_annualized_return_cagr"],
        expected_session_cagr,
        "252-session CAGR",
    )
    expected_calendar_cagr = (
        metrics["final_equity"] ** (365.2425 / holdout["elapsed_calendar_days"]) - 1.0
    )
    _close(
        metrics["calendar_annualized_return_cagr"],
        expected_calendar_cagr,
        "calendar-time CAGR",
    )
    _close(
        metrics["session_calmar_ratio"],
        metrics["session_annualized_return_cagr"] / abs(metrics["max_drawdown"]),
        "252-session Calmar",
    )
    _close(
        metrics["calendar_calmar_ratio"],
        metrics["calendar_annualized_return_cagr"] / abs(metrics["max_drawdown"]),
        "calendar-time Calmar",
    )
    per_symbol_accuracy = holdout["per_symbol_raw_accuracy"]
    if tuple(per_symbol_accuracy) != SYMBOLS:
        raise ReferenceValidationError("per-symbol accuracy order changed")
    _close(
        holdout["mean_per_symbol_raw_accuracy"],
        sum(per_symbol_accuracy.values()) / len(per_symbol_accuracy),
        "mean per-symbol raw accuracy",
    )

    return [
        "dataset_provenance",
        "frozen_feature_schema",
        "continuous_walk_forward_and_cost_boundary",
        "holdout_metric_arithmetic",
        "calendar_and_session_calmar_conventions",
        "archived_holdout_accuracy",
    ]


def validate_claim_ledger(ledger: dict[str, Any]) -> list[str]:
    if ledger.get("schema_version") != "1.0.0":
        raise ReferenceValidationError("unsupported claim-ledger schema")
    records = ledger.get("claims")
    if not isinstance(records, list):
        raise ReferenceValidationError("claim ledger must contain a list")
    by_id = {record["id"]: record for record in records}
    expected = {
        "historical_calmar": "supported_descriptive_post_run_metric",
        "holdout_raw_accuracy": "supported_descriptive_archived_metric",
        "validated_alpha_or_future_performance": "not_claimed",
        "physical_hardware_performance": "not_tested",
        "public_end_to_end_rerun": "not_available",
    }
    if {key: by_id[key]["status"] for key in expected if key in by_id} != expected:
        raise ReferenceValidationError("claim statuses differ from the frozen scope")
    if "55.24" not in by_id["holdout_raw_accuracy"]["claim"]:
        raise ReferenceValidationError("holdout accuracy claim lost its sample identity")
    return list(expected)


def compare_holdout_analysis(analysis: dict[str, Any], reference: dict[str, Any]) -> None:
    expected = reference["historical_holdout"]
    metrics = expected["portfolio_metrics"]
    for key in ("first_date", "last_date", "n_days", "n_symbols"):
        if analysis[key] != expected[key]:
            raise ReferenceValidationError(
                f"private holdout {key} mismatch: expected {expected[key]}, got {analysis[key]}"
            )
    mappings = {
        "final_equity": "final_equity",
        "total_return": "total_return",
        "annualized_return_cagr": "session_annualized_return_cagr",
        "annualized_return_arithmetic": "session_annualized_return_arithmetic",
        "annualized_volatility": "session_annualized_volatility",
        "net_sharpe": "net_sharpe",
        "max_drawdown": "max_drawdown",
        "calmar_ratio": "session_calmar_ratio",
        "calendar_annualized_return_cagr": "calendar_annualized_return_cagr",
        "calendar_calmar_ratio": "calendar_calmar_ratio",
    }
    for actual_key, expected_key in mappings.items():
        _close(
            analysis[actual_key],
            metrics[expected_key],
            f"private holdout {actual_key}",
            tolerance=2e-12,
        )
