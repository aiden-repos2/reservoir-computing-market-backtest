import csv

import pytest

from reservoir_market_backtest.schema import (
    TARGET_COLUMNS,
    FeatureSchemaError,
    base_feature_columns,
    select_and_validate_base_features,
    validate_feature_csv,
)


def test_frozen_feature_counts_and_exact_selection() -> None:
    assert len(base_feature_columns("SPY")) == 39
    assert len(base_feature_columns("QQQ")) == 40
    header = (
        "Date",
        *base_feature_columns("QQQ"),
        *TARGET_COLUMNS,
    )
    selected = select_and_validate_base_features(header, "QQQ")
    assert selected == base_feature_columns("QQQ")


def test_schema_rejects_missing_reordered_and_unknown_columns() -> None:
    expected = base_feature_columns("SPY")
    with pytest.raises(FeatureSchemaError):
        select_and_validate_base_features((*reversed(expected), *TARGET_COLUMNS), "SPY")
    with pytest.raises(FeatureSchemaError):
        select_and_validate_base_features((*expected, *TARGET_COLUMNS, "surprise"), "SPY")
    with pytest.raises(FeatureSchemaError):
        select_and_validate_base_features((*expected[:-1], *TARGET_COLUMNS), "SPY")


def test_private_csv_validation_reads_header_only(tmp_path) -> None:
    path = tmp_path / "SPY.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("Date", *base_feature_columns("SPY"), *TARGET_COLUMNS))
        writer.writerow(("not-inspected", "private-row-not-needed"))
    assert validate_feature_csv(path, "SPY") == base_feature_columns("SPY")
