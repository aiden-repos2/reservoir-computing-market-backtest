# Data sources and rights

## Historical inputs

The historical experiment used:

- daily OHLCV records for `SPY`, `QQQ`, `XLK`, `XLF`, `XLE`, `XLV`, `XLI`,
  `TLT`, and `GLD`, acquired through a `yfinance` fallback after direct Stooq
  acquisition became unreliable;
- FRED series `DGS2`, `DGS10`, `T10Y2Y`, `DFF`, `BAMLH0A0HYM2`,
  `DCOILWTICO`, `VIXCLS`, and `DTWEXBGS`;
- the U.S. daily Economic Policy Uncertainty index; and
- the daily Geopolitical Risk index and its acts and threats components.

The derived model-input contract is documented in
[`METHOD.md`](METHOD.md). Historical observation rows and derived feature
matrices are not included in this repository.

## Included material

The repository contains author-created source code, a frozen configuration,
aggregate historical statistics, synthetic fixtures, retained-file hashes,
documentation, and tests. It excludes:

- downloaded OHLCV, FRED, EPU, and GPR observations;
- source-derived feature and target rows;
- dated instrument-level return arrays;
- model states, fitted readout weights, and runtime caches; and
- any third-party file whose redistribution rights have not been established.

These exclusions are a conservative release decision, not a legal conclusion
about any specific fact or file.

## No acquisition workflow

No third-party downloader or fresh-acquisition workflow is shipped. Current
source terms can restrict automated access, storage, redistribution, or use in
software and machine-learning development. Before acquiring data, a user must
independently review the then-current terms for every source and series and
obtain any necessary permission. Nothing in this repository grants that
permission.

Even where separately authorized, a fresh download may not recreate the
historical inputs. Vendors can revise observations, corporate-action
adjustments, endpoints, and terms. A new acquisition should record the source,
retrieval time, query, response hash, applicable terms, and transformations.

## Licenses

- Author-created source code: MIT, subject to `LICENSE`.
- Author-controlled documentation and aggregate result expression: CC BY 4.0,
  subject to `RESULTS_LICENSE.md`.
- Third-party and excluded material: no license is granted by this repository.

Names and tickers identify sources and instruments only. Their use does not
imply sponsorship, endorsement, or affiliation. Source-specific notices are in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
