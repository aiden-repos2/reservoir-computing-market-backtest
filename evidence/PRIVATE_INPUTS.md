# Private evidence inventory

The historical return arrays and source-derived feature rows are retained
outside this public package. Their recorded hashes establish file identity;
they do not grant redistribution rights.

## Historical return series

Two byte representations contain the same 36 named arrays: dates and net
strategy returns for the Ikeda and linear-readout arms across nine instruments.

| Profile | Bytes | SHA-256 | Notes |
|---|---:|---|---|
| Original archive | 190,390 | `c8f5c0081ab0e28d834b5b41d5263f1060ac5611a3cadd8c7905e2a40c800a1f` | Uncompressed NPZ written with the historical holdout |
| Minimized private copy | 156,002 | `fcce06f796e2c11df63766d8c2e2e27aadffa408b53ba60aef7b0c0e23634714` | Compressed NPZ; all 36 arrays equal the original |

The metric replay accepts either profile only after checking its exact size
and hash. It then verifies required array names, alignment, unique dates, and
finite return values before calculating the equal-weight portfolio metrics.

## Aggregate record

| File | Bytes | SHA-256 |
|---|---:|---|
| `holdout.json` | 10,014 | `36f6858f611997027cc40fc06d26268c5b3d62a504f16bb7b09da0a4c92f2772` |

The reviewed public record in `results/reference_results.json` contains only
aggregate values needed to describe and verify the historical result.

## Feature rows

Raw and source-derived market feature rows are not distributed. The exact
ordered column contract is recorded in `config/frozen_method.json` and
`src/reservoir_market_backtest/schema.py`, but public verification does not
claim a fresh data-to-result refit.

## Handling rules

- Never commit private arrays, feature rows, symlinks to them, or archives
  containing them.
- Never print full arrays or private absolute paths in automated logs.
- Open retained evidence read-only and write any reports elsewhere.
- Fail closed on an unknown size, hash, schema, date range, or nonfinite value.
- Do not fetch a replacement automatically when private evidence is absent.
