# Reproducibility

This repository distinguishes code execution, metric replay, and a complete
historical rerun.

## Code and record verification

From a clean checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
pytest -q
python scripts/verify_release.py
python scripts/report_results.py
```

These commands test the reservoir, ridge readout, position rule, metric
definitions, feature schema, aggregate result record, and exact public release
manifest. They do not download third-party data or refit the historical model.

## Synthetic end-to-end execution

```bash
python examples/synthetic_demo.py
```

The deterministic example generates synthetic features and returns, computes
Ikeda reservoir states, fits the walk-forward ridge readout, constructs
simulated strategy returns, and reports metrics. It demonstrates that the
software path executes without presenting synthetic values as market results.

## Exact replay of reported path metrics

The author retains `holdout_series.npz`, which contains dated per-instrument
net strategy returns for the historical holdout. It is not distributed. With
an authorized local copy, the path metrics can be recomputed by running:

```bash
python scripts/recompute_metrics.py \
  --series /secure/path/holdout_series.npz
```

The script accepts only a recognized byte identity, validates the required
array names and dates, and opens the file read-only. It then joins the nine
instrument series on common dates, equal-weights them, and recomputes total
return, annualized return, volatility, Sharpe, maximum drawdown, and both
Calmar conventions.

## Authorized feature files

Users who already possess authorized feature files can validate their headers:

```bash
python scripts/validate_feature_schema.py /path/to/feature_csv_directory
```

This checks the ordered 39-column `SPY` contract, the ordered 40-column
contract for each other instrument, and the target columns. It does not compare
row values with the historical inputs or establish a historical rerun.

## Complete historical rerun boundary

A byte-identical public data-to-result rerun is not claimed because:

1. Third-party observations and source-derived historical feature rows are not
   distributed.
2. The complete transitive dependency and native build environment were not
   locked when the historical run was executed.
3. Upstream financial and macroeconomic series can be revised or served
   differently over time.

Accordingly, the public checkout supports method inspection, synthetic
execution, aggregate-record verification, and optional exact metric replay
from the retained return series. A run on newly acquired or independently
constructed inputs is a new retrospective experiment and should receive its
own result identity.
