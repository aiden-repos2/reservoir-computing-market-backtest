# Limitations

## Study scope

- **One fixed retrospective experiment.** The result applies to one simulated
  reservoir configuration, feature set, instrument panel, and historical
  period.
- **Short holdout.** The 628-session holdout covers about two and a half years
  and cannot represent the full range of market regimes.
- **Low realized volatility.** Annualized portfolio volatility was about
  1.61%, while the maximum drawdown was about 1.69%. The Calmar ratio is
  sensitive to this small denominator.
- **Correlated instruments.** The nine ETFs do not represent nine independent
  bets; several share substantial broad-market exposure.
- **Model selection.** The fixed configuration followed a broader development
  search. Historical holdout results should not be generalized beyond the
  stated pipeline and period.
- **Historical data revisions.** Some market and macroeconomic histories may
  reflect later revisions and are not proven point-in-time vintages.

## Simulation scope

- No physical reservoir hardware was measured.
- No orders were sent to a broker and no capital was traded live.
- The cost model used a flat 2.5-basis-point charge on position changes.
- Market impact, order-book depth, nonlinear slippage, rejected orders,
  financing, leverage constraints, borrow availability, taxes, and operational
  failures were not modeled.
- Scaling a low-volatility simulated return path can change both Sharpe and
  Calmar once financing, gaps, and market impact are included.

## Statistical scope

- The nine instrument series share dates and market drivers; cross-instrument
  observations should not be treated as independent samples.
- The fixed sigmoid applied to ridge scores was not fitted probability
  calibration, so absolute probability-score interpretations require caution.
- Raw classification accuracy and portfolio return are different quantities.
  Accuracy alone cannot determine Sharpe, drawdown, or Calmar without the
  complete ordered return path and position rule.
- Calmar depends on the annualization convention. Both elapsed-calendar-time
  and 252-session values are reported.

## Appropriate interpretation

The supported statement is:

> In a fixed retrospective simulation covering 628 holdout sessions, the
> nine-instrument reservoir-computing portfolio produced a 5.7199% total
> return, 1.3930 net Sharpe ratio, -1.6863% maximum drawdown, and an
> elapsed-calendar-time Calmar ratio of 1.3299.

These statistics describe one historical simulated path. They are not live
performance, investment advice, a trading recommendation, or a guarantee of
future returns or persistent alpha.
