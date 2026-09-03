"""Frozen 39/40-column feature-input contract for the historical result."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


SYMBOLS = ("SPY", "QQQ", "XLK", "XLF", "XLE", "XLV", "XLI", "TLT", "GLD")

COMMON_BASE_FEATURES = (
    "p_ret1", "p_ret2", "p_ret3", "p_ret5", "p_ret10", "p_ret21",
    "p_mom21", "p_mom63", "p_mom126", "p_mom252", "p_52wd", "p_rev5",
    "p_volz", "p_ovn", "v_gk1", "v_gk5", "v_gk21", "v_vov", "v_pkgk",
)
CALENDAR_FEATURES = ("c_dow", "c_meom")
MACRO_GEO_FEATURES = (
    "m_DGS2_d", "m_DGS10_d", "m_T10Y2Y", "m_T10Y2Y_d5", "m_DFF_d",
    "m_BAMLH0A0HYM2_d", "m_DCOILWTICO_r", "m_VIXCLS", "m_VIXCLS_d5",
    "m_DTWEXBGS_r", "g_epu", "g_epu_d5", "g_gpr", "g_gpr_d5",
    "g_gpra", "g_gpra_d5", "g_gprt", "g_gprt_d5",
)
TARGET_COLUMNS = ("y_dir", "y_lvol", "y_lvol5", "y_ret_next", "y_sig_now")


class FeatureSchemaError(ValueError):
    """Raised when private feature files do not match the frozen contract."""


def base_feature_columns(symbol: str) -> tuple[str, ...]:
    """Return the exact ordered model-input columns for a symbol."""

    normalized = symbol.upper()
    if normalized not in SYMBOLS:
        raise FeatureSchemaError(f"unsupported symbol: {symbol}")
    cross = () if normalized == "SPY" else ("x_corrspy",)
    return COMMON_BASE_FEATURES + cross + CALENDAR_FEATURES + MACRO_GEO_FEATURES


def select_and_validate_base_features(
    columns: Iterable[str],
    symbol: str,
) -> tuple[str, ...]:
    """Select historical inputs and reject missing, reordered, or unknown fields."""

    observed = tuple(str(column) for column in columns if str(column) != "Date")
    allowed = set(base_feature_columns(symbol)) | set(TARGET_COLUMNS)
    unknown = tuple(column for column in observed if column not in allowed)
    if unknown:
        raise FeatureSchemaError(f"unknown columns for {symbol}: {unknown}")

    selected = tuple(
        column
        for column in observed
        if not column.startswith("y_")
    )
    expected = base_feature_columns(symbol)
    if selected != expected:
        missing = tuple(column for column in expected if column not in selected)
        raise FeatureSchemaError(
            f"base feature schema mismatch for {symbol}; "
            f"expected {len(expected)} ordered columns, observed {len(selected)}; "
            f"missing={missing}"
        )

    observed_targets = tuple(column for column in observed if column.startswith("y_"))
    if observed_targets != TARGET_COLUMNS:
        raise FeatureSchemaError(
            f"target schema mismatch for {symbol}: {observed_targets}"
        )
    return selected


def validate_feature_csv(path: str | Path, symbol: str) -> tuple[str, ...]:
    """Validate only a private CSV header; row values are never retained."""

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise FeatureSchemaError(f"empty feature file: {csv_path}") from exc
    if not header or header[0] != "Date":
        raise FeatureSchemaError(f"first column must be Date: {csv_path}")
    return select_and_validate_base_features(header, symbol)
