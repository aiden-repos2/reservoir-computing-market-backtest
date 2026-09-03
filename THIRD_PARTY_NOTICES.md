# Third-party data notices

This repository does not distribute third-party observations or
source-derived feature rows. The table below documents why. It is a
conservative release record, not legal advice or a grant of rights. Terms can
change; a user who acquires fresh data must review the terms then in force.

| Source used historically | Notice reviewed 2026-09-03 | Repository treatment |
|---|---|---|
| Yahoo Finance, accessed through `yfinance` | The [`yfinance` documentation](https://ranaroussi.github.io/yfinance/) says the package is unaffiliated with Yahoo, is intended for research and education, and that Yahoo Finance API data are intended for personal use. [Yahoo's Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html) separately restrict automated collection and reuse except with permission. | No Yahoo observations, cache, or downloader are shipped. Tickers appear only as factual instrument identifiers. |
| FRED and underlying providers | As reviewed on the date above, the [FRED terms](https://fred.stlouisfed.org/legal/terms/) prohibit using FRED Services or Content in connection with development or training of software or machine-learning systems and prohibit storing, caching, or archiving FRED Content under the stated service and API rules. They also require attribution and preserve additional restrictions imposed by each series owner. | No FRED observations, source-derived rows, downloader, or fresh-acquisition workflow are shipped. Any future use requires an independent review of the then-current terms and any necessary permission; this repository does not authorize it. |
| ICE Data Indices via FRED | The [ICE BofA high-yield spread series page](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) identifies the data as copyrighted, limits top-level data to internal use, and prohibits reproduction or third-party distribution without prior written approval. | The downloaded spread series and rows derived from it are excluded. Aggregate backtest statistics do not reproduce the series. |
| U.S. Economic Policy Uncertainty index | The [official U.S. EPU page](https://www.policyuncertainty.com/us_monthly.html) labels its work CC BY 4.0 and explains that recent daily values can be revised. | No EPU observations are shipped. Any future release would need attribution, a retrieval date, and an immutable source snapshot or hash. |
| Caldara-Iacoviello Geopolitical Risk index | The [official GPR page](https://www.matteoiacoviello.com/gpr.htm) offers its webpage material under a Creative Commons Attribution license and asks users to cite Caldara and Iacoviello (2022), the website, and the download date. | No GPR, threats, or acts observations are shipped. Any future release would need the requested attribution and retrieval date. |

## No endorsement

Yahoo, FRED, the Federal Reserve Bank of St. Louis, ICE Data Indices, Bank of
America, the EPU authors, the GPR authors, and the named fund issuers do
not sponsor, endorse, or certify this repository. Their names and marks are
used only to identify historical inputs and applicable terms.

## Software is separate from data

The MIT license in `LICENSE` applies only to author-created software and the
code-adjacent files defined there. The CC BY 4.0 grant in
`RESULTS_LICENSE.md` applies only to the author-controlled material defined
there. Neither license reaches an excluded third-party observation, database,
mark, or source-derived row.
