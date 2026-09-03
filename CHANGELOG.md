# Changelog

All notable changes to this project are recorded here. The project uses
semantic versioning for software releases.

## [1.0.0] - 2026-09-03

### Added

- Deterministic Python implementation of the simulated Ikeda-type reservoir,
  binary input mask, ridge readout, and expanding walk-forward schedule.
- Portfolio-return and financial-metric functions with explicit annualization,
  Sharpe, maximum-drawdown, and Calmar definitions.
- Frozen configuration and feature-schema contracts for the historical model.
- Machine-readable record of the 628-session historical holdout result.
- Optional, hash-gated metric replay from the retained holdout return series.
- Deterministic synthetic example, automated tests, continuous integration,
  and an exact public-release manifest.
- Method, result, limitation, reproducibility, and data-rights documentation.

### Historical result documented

- Simulated net return under the stated cost rule: 5.7199%.
- Net Sharpe ratio: 1.3930 using 252-session annualization.
- Maximum drawdown: -1.6863%.
- Calmar ratio: 1.3299 using elapsed calendar time and 1.3385 using the
  252-session convention.

### Release boundary

- Third-party observations and source-derived feature rows are excluded.
- No downloader is shipped; source terms must be reviewed independently.
- The public checkout supports synthetic execution and aggregate verification,
  but does not claim a byte-identical historical data-to-result rerun.
