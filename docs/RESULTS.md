# Historical results

## Portfolio path

The historical holdout combined nine simulated net-return series on 628 common
sessions from 2024-01-02 through 2026-07-06. The portfolio equally weighted the
nine instruments after the per-instrument position and transaction-cost rule
was applied.

| Metric | Exact value |
|---|---:|
| Initial equity | 1.000000000000000 |
| Final equity | 1.057198913169459 |
| Total return | 0.057198913169459 |
| Calendar-time CAGR | 0.022426642052923 |
| 252-session geometric annualized return | 0.022570962448750 |
| 252-session arithmetic annualized mean | 0.022450721737689 |
| 252-session annualized volatility | 0.016116934814070 |
| Net Sharpe ratio | 1.392989547745175 |
| Maximum drawdown | -0.016863048336925 |
| Calendar-time Calmar ratio | 1.329928112926981 |
| 252-session Calmar ratio | 1.338486494124920 |

The maximum-drawdown peak occurred on 2024-12-03 and the trough on 2025-04-07.

## Raw holdout classification accuracy

The historical summary also recorded these per-instrument raw accuracies over
628 sessions per instrument:

| Instrument | Accuracy |
|---|---:|
| SPY | 0.5732 |
| QQQ | 0.5780 |
| XLK | 0.5971 |
| XLF | 0.5494 |
| XLE | 0.5557 |
| XLV | 0.5016 |
| XLI | 0.5430 |
| TLT | 0.5032 |
| GLD | 0.5701 |
| Unweighted mean of the displayed values | 0.55237 |

Accuracy and portfolio performance are different quantities. The Calmar ratio
comes from the complete ordered net-return path, not from converting the
accuracy percentage. Accuracy used the strict comparison `next return > 0`, so
an exactly unchanged next-session value was classified as non-up.

## Calmar convention

The primary reported Calmar value uses elapsed calendar time:

```text
calendar_CAGR = final_equity ** (365.2425 / 916) - 1
calendar_Calmar = calendar_CAGR / abs(maximum_drawdown)
                = 1.329928112926981.
```

Using 252 trading sessions per year instead gives 1.338486494124920. Both
support the concise description **approximately 1.33**. The annualization
choice should be stated whenever more precision is quoted.

## Scope

These figures are historical simulated results for one fixed pipeline and
holdout period. They are not live performance, a forecast, investment advice,
or a guarantee of future returns or persistent alpha.
