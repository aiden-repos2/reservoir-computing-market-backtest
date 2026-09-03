# Reservoir Computing Market Backtest

![Status: retrospective research](https://img.shields.io/badge/status-retrospective%20research-355c7d)
![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-green)](LICENSE)

Research software for a retrospective market backtest built around a
simulated Ikeda-type delay reservoir, an expanding-window ridge readout, and a
volatility-scaled portfolio rule.

On the fixed historical holdout from 2024-01-02 through 2026-07-06, the
simulated nine-instrument portfolio produced a **5.7199% total return**, a
**1.3930 net Sharpe ratio**, a **-1.6863% maximum drawdown**, and a Calmar ratio
of approximately **1.33**. These are statistics for one retrospective
simulation. They are not live performance, a forecast, or a guarantee of
future returns or persistent alpha.

## Historical result

The portfolio joined nine simulated net-return series on 628 common trading
sessions and weighted them equally.

| Quantity | Historical value |
|---|---:|
| Instruments | 9 exchange-traded funds |
| Holdout interval | 2024-01-02 to 2026-07-06 |
| Trading sessions | 628 |
| Total simulated return | 5.7199% |
| Annualized return, elapsed-calendar-time convention | 2.2427% |
| Annualized return, 252-session convention | 2.2571% |
| Annualized volatility, 252-session convention | 1.6117% |
| Net Sharpe, 252-session convention | 1.3930 |
| Maximum drawdown | -1.6863% |
| Calmar, elapsed-calendar-time convention | **1.3299** |
| Calmar, 252-session convention | 1.3385 |
| Mean raw holdout accuracy across the nine instruments | 55.24% |

The calendar-time Calmar uses 916 elapsed days between the first and last
holdout sessions. The 252-session version treats 252 observations as one year.
The concise value is therefore **approximately 1.33**; rounded to one decimal
place, it is 1.3 rather than 1.4. The Calmar statistic was computed after the
historical run from the retained ordered return series.

See [the complete results record](docs/RESULTS.md) for exact values and the
drawdown dates.

## System design

The historical pipeline used:

1. Daily OHLCV-derived market features for `SPY`, `QQQ`, `XLK`, `XLF`, `XLE`,
   `XLV`, `XLI`, `TLT`, and `GLD`.
2. Lagged macroeconomic, policy-uncertainty, and geopolitical-risk features.
3. Zero-filling of missing feature values, followed by a fixed binary input
   mask feeding a simulated Ikeda-type delay reservoir with 200 virtual nodes.
4. An expanding-window ridge readout, refitted every 21 sessions with a
   five-session embargo.
5. A confidence-scaled position capped at an absolute weight of one, a 10%
   annualized volatility target, and a simulated cost of 2.5 basis points per
   unit of absolute position change.
6. Equal weighting across the nine instruments on common dates.

The direction-readout walk-forward schedule began in 2016 and continued
without resetting through the later data. The development evaluation covered
2016-01-01 through 2023-12-31; after every row had been scored under that
schedule and the corresponding position-and-cost stream had been formed, the
chronologically later 2024-01-02 through 2026-07-06 rows were selected as the
historical holdout. Neither the readout nor the simulated position was reset at
the holdout boundary. No physical reservoir hardware and no live brokerage
account were used.

Full equations, parameters, feature groups, and metric definitions are in
[`docs/METHOD.md`](docs/METHOD.md). The frozen machine-readable configuration
is in [`config/frozen_method.json`](config/frozen_method.json).

## Install and verify

```bash
cd reservoir-computing-market-backtest
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
pytest -q
python scripts/verify_release.py
python scripts/report_results.py
```

The verification command checks metric implementations, result-record
consistency, and the exact public release manifest. It does not download market
data or rerun the historical experiment.

The installed command-line entry point provides the same release check:

```bash
reservoir-market-backtest
```

## Run the model on synthetic data

The repository includes a deterministic example that exercises the reservoir,
walk-forward readout, position rule, and metric functions without third-party
data:

```bash
python examples/synthetic_demo.py
```

The example labels its output as synthetic. Its numbers are not part of the
historical result.

## Use authorized feature files

No third-party data downloader is included. Users who independently possess
authorized feature files can check their headers against the frozen input
contract:

```bash
python scripts/validate_feature_schema.py /path/to/feature_csv_directory
```

The directory must contain one `SYMBOL.csv` file for each of the nine
instruments. Each file begins with `Date`, contains the ordered feature columns
defined in [`docs/METHOD.md`](docs/METHOD.md), and includes the documented
target columns. Schema validation checks structure only; it does not establish
that a file contains the historical observations or reproduce the historical
run.

## Replay the historical path metrics

The dated per-instrument return arrays are not distributed. If an authorized
copy of the retained `holdout_series.npz` is available locally, the reported
portfolio statistics can be recomputed without changing the source file:

```bash
python scripts/recompute_metrics.py \
  --series /secure/path/holdout_series.npz
```

The script verifies the file identity and schema before reading it. Details are
in [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## What is and is not reproducible

- A clean checkout can run the model on synthetic features, exercise the
  backtest and metric code, and verify the published aggregate record.
- The retained return series permits exact replay of the reported path metrics
  when supplied separately.
- A byte-identical data-to-result rerun is not claimed from the public
  checkout. Third-party observations and source-derived feature rows are not
  redistributed, and the complete historical software environment was not
  locked at run time.

The boundary is described in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) and
[`docs/DATA_AND_RIGHTS.md`](docs/DATA_AND_RIGHTS.md).

## Repository map

```text
src/          reservoir, readout, portfolio, metric, and verification code
config/       frozen method and evaluation parameters
scripts/      result reporting, metric replay, schema, and release utilities
results/      machine-readable historical result records
evidence/     retained-file identities and public release manifest
docs/         method, results, limitations, reproducibility, and data rights
examples/     deterministic synthetic demonstration
tests/        numerical, schema, model, and release tests
```

## Scope and limitations

- This is one fixed retrospective simulation over a relatively short holdout.
- The realized annualized volatility was only about 1.61%, so the Calmar ratio
  is sensitive to its small drawdown denominator.
- The nine instruments are correlated and do not represent nine independent
  bets.
- The simulation uses simplified transaction costs and omits market impact,
  nonlinear slippage, financing, borrow constraints, taxes, and operational
  failures.
- Historical source series may have been revised and are not proven
  point-in-time vintages.
- No physical device or live trading system was tested.

Nothing in this repository is investment advice or a trading recommendation.
Historical simulated performance does not guarantee future results. See
[`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) before using or quoting the
metrics.

## Citation and licensing

Use [`CITATION.cff`](CITATION.cff) when citing the software.

Author-created code is licensed under the MIT License. Author-controlled
documentation and aggregate result expression are offered under CC BY 4.0,
subject to [`RESULTS_LICENSE.md`](RESULTS_LICENSE.md). Third-party observations
and source-derived feature rows are not distributed or relicensed. The
source-specific boundary is recorded in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
