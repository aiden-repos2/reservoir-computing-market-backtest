# Method

This document specifies the historical simulated market-backtest pipeline.

## Instruments and periods

The panel contained nine exchange-traded funds: `SPY`, `QQQ`, `XLK`, `XLF`,
`XLE`, `XLV`, `XLI`, `TLT`, and `GLD`.

- Development evaluation: 2016-01-01 through 2023-12-31.
- Historical holdout: 2024-01-02 through 2026-07-06.
- Common holdout sessions: 628.
- Readout refit interval: 21 sessions.
- Embargo before each evaluated block: 5 sessions.

All splits were chronological. The direction-readout schedule began at the
2016 development boundary and used an expanding training window. It continued
without resetting into 2024 and later data. After the walk-forward predictions
and the continuous position-and-cost stream had been formed, rows dated
2024-01-02 through 2026-07-06 were selected for the reported holdout
statistics. Neither the readout schedule nor the simulated position was reset
at the holdout boundary.

## Feature contract

The historical feature builder began with daily ETF OHLCV records and joined
lagged macroeconomic, policy-uncertainty, and geopolitical-risk fields. Model
inputs were ordered as follows.

### Price and technical fields

`p_ret1`, `p_ret2`, `p_ret3`, `p_ret5`, `p_ret10`, `p_ret21`, `p_mom21`,
`p_mom63`, `p_mom126`, `p_mom252`, `p_52wd`, `p_rev5`, `p_volz`, `p_ovn`,
`v_gk1`, `v_gk5`, `v_gk21`, `v_vov`, and `v_pkgk`.

### Cross-instrument and calendar fields

Every non-`SPY` instrument also used `x_corrspy`. All instruments used
`c_dow` and `c_meom`.

### Macroeconomic and uncertainty fields

`m_DGS2_d`, `m_DGS10_d`, `m_T10Y2Y`, `m_T10Y2Y_d5`, `m_DFF_d`,
`m_BAMLH0A0HYM2_d`, `m_DCOILWTICO_r`, `m_VIXCLS`, `m_VIXCLS_d5`,
`m_DTWEXBGS_r`, `g_epu`, `g_epu_d5`, `g_gpr`, `g_gpr_d5`, `g_gpra`,
`g_gpra_d5`, `g_gprt`, and `g_gprt_d5`.

This gives 39 input columns for `SPY` and 40 for each other instrument. The
associated target columns were `y_dir`, `y_lvol`, `y_lvol5`, `y_ret_next`, and
`y_sig_now`. `Date` was the first CSV column and was not a model input.

After rows lacking `y_ret_next` were removed, missing values in the feature
matrix were replaced with `0.0` before the reservoir transformation. No
additional feature standardization was applied to this fixed Ikeda
configuration.

The direction target was the sign of the next-session log adjusted-close
return: -1 for a decline, 0 for an unchanged value, and +1 for an increase.
Feature files are not distributed; the schema is provided so authorized
inputs can be checked without guessing the model surface.

### Feature transformations

Most continuous inputs used the same bounded rolling transform. For a source
series `q`, the value at session `t` was

```text
z_t = tanh(clip((q_t - rolling_mean_252) / (rolling_sd_252 + 1e-12),
                -5, +5) / 2),
```

with a minimum of 60 observations in the 252-row window and the window ending
at `t`. Price returns and momentum were log adjusted-close changes over the
named horizon. `p_52wd` was the log distance from the rolling 252-session high;
`p_rev5` was the negative five-session log return; `p_volz` transformed log
volume; and `p_ovn` transformed the log ratio of the current open to the prior
close. `x_corrspy` transformed the trailing 21-session return correlation with
`SPY`. `c_dow` encoded Monday through Friday from -0.5 through +0.5, and
`c_meom` indicated the final trading session of a month.

The Garman--Klass daily volatility estimate was

```text
sigma_GK = sqrt(max(0.5*log(H/L)^2
                    - (2*log(2)-1)*log(C/O)^2, 1e-10)).
```

`v_gk1` transformed `log(sigma_GK)`; `v_gk5` and `v_gk21` transformed its
trailing 5- and 21-session means; `v_vov` transformed its trailing 21-session
standard deviation; and `v_pkgk` transformed the log ratio of Parkinson to
Garman--Klass volatility.

For macroeconomic fields, yields, the federal-funds rate, and the high-yield
spread used first differences except that the term spread also retained its
level and five-row difference. Oil and the dollar index used log differences.
VIX retained its level and five-row difference. EPU and each GPR component
used its level and five-row difference. These source fields were transformed
as above, shifted by one source-date row before joining to instrument dates,
and forward-filled on the combined feature table.

## Simulated Ikeda reservoir

For feature vector `z_t`, a fixed binary mask formed a held drive for each
virtual node. Within each node, the historical semi-explicit Euler loop used

```text
forcing = beta * sin(delayed_x + masked_input + phase_offset)^2
x <- x + dt * (-x - delta*y + forcing)
y <- y + dt * x
```

The current `x` value was sampled after the integration steps for each virtual
node. With the selected `delta = 0`, the auxiliary state did not feed back into
the primary state; the implementation is therefore described as Ikeda-type
rather than as a physical band-pass realization.

For `d` input columns, the mask was a `200 x d` matrix sampled as -1 or +1
with NumPy's seeded default random generator, then multiplied by the input
scale. Each masked node drive was held for 10 integration steps. The circular
delay history had `200 * 10 + 7 = 2007` entries initialized to zero, with
initial states `x = 0.1` and `y = 0.0`.

| Parameter | Value |
|---|---:|
| Virtual nodes | 200 |
| Integration steps per node | 10 |
| Step size `dt` | 0.08661933269857963 |
| Feedback gain `beta` | 0.3441984642966166 |
| Phase offset | 1.1583611813967833 |
| Input scale | 0.013175730055118363 |
| Auxiliary parameter `delta` | 0.0 |
| Desynchronization | 7 |
| Mask type | Binary, -1 or +1 |
| Mask seed | 1234 |

The machine-readable values are in `config/frozen_method.json`.

## Ridge readout

Reservoir states were passed to a ridge readout with penalty 1.0. The intercept
was included in the penalized design matrix. The first scored block began at
the 2016 development boundary. At each evaluation block, the readout was fitted
only on earlier rows ending five sessions before the block, then refitted every
21 sessions. This expanding schedule continued through the end of the series;
it was not restarted at the 2024 holdout boundary.

With a column of ones appended to the state matrix `A`, the fitted weights were

```text
w = solve(A' A + 1.0 * I, A' y).
```

A raw ridge score `s` was transformed by the fixed monotone map

```text
p_up = 1 / (1 + exp(-4*s)).
```

This was a position-sizing transform, not a separately fitted probability
calibration. Absolute probability-score interpretations therefore require
caution.

## Portfolio rule

For each instrument, the pipeline formed

```text
confidence = 2 * (p_up - 0.5)
daily_volatility_target = 0.10 / sqrt(252)
position = clip(confidence * daily_volatility_target / volatility_forecast,
                -1, +1).
```

The volatility forecast came from a causal HAR-style ridge readout using
current log volatility and trailing 5- and 21-session means to predict
next-session log volatility. It used an initial 504-session training window, a
penalty of 0.0001, a penalized intercept, 21-session refits, and a five-session
embargo. Before the first fitted forecast, the current log-volatility value was
the fallback. To match the historical construction, incomplete values at the
start of each 5- or 21-session rolling-mean series were filled with that
series's first complete window mean; these early rows preceded the 504-session
forecast threshold.

The simulation subtracted 2.5 basis points times the absolute change in
position. Position changes and transaction costs were computed continuously
from the start of the walk-forward score stream, including its entry from an
initial zero position. The 2024 holdout was sliced only after this calculation,
so its first position change was measured from the preceding simulated
position rather than from a new zero position. The nine holdout net-return
series were then joined on common dates and equally weighted.

## Metric definitions

Raw directional accuracy compared `p_up > 0.5` with
`next_session_return > 0`; an exactly unchanged next-session value therefore
belonged to the non-up class.

For chronological daily net returns `r_t`, equity is

```text
equity_t = product(1 + r_i), i <= t.
```

Maximum drawdown is the minimum percentage decline from the running equity
peak, including initial equity of one. Net Sharpe uses the sample standard
deviation, a zero risk-free rate, and 252 sessions per year:

```text
Sharpe = mean(r) / sample_std(r) * sqrt(252).
```

Two annualization conventions are reported for Calmar.

```text
calendar_CAGR = final_equity ** (365.2425 / elapsed_calendar_days) - 1
session_CAGR  = final_equity ** (252 / number_of_sessions) - 1
Calmar        = CAGR / abs(maximum_drawdown).
```

They produce Calmar values of 1.3299 and 1.3385, respectively. A concise
summary should state approximately 1.33 and name the convention when giving
more precision.
