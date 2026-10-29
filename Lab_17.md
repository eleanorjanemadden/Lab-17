# Lab 17 — Point-in-Time Audit

Eleanor Madden | October 29, 2026

## D — Define

**Was each number in my series knowable on the day I would have traded on it — and may Project 2 use it?**

My answer is yes only when the value appears in the vintage available by the decision date. I chose **GS10**, the monthly 10-year Treasury yield, for my BIL/IEF/LQD/VT universe. Higher Treasury yields can lower the prices of existing bonds, which matters for IEF and LQD. They can also affect equity valuations. This is a reason to investigate the series, not evidence that it predicts returns.

Lab 16 taught me to filter by publication date before selecting a revision. This app applies that idea to real data by requesting an ALFRED vintage instead of cutting today's FRED file at an old observation date. The earlier lab files are preserved.

## R — Represent: my data card

| Field | GS10 |
|---|---|
| Source and links | Board of Governors of the Federal Reserve System, distributed by [FRED](https://fred.stlouisfed.org/series/GS10) and [ALFRED](https://alfred.stlouisfed.org/series?seid=GS10); release: [H.15 Selected Interest Rates](https://www.federalreserve.gov/releases/h15/) |
| Measure | Market yield on U.S. Treasury securities at 10-year constant maturity, quoted on an investment basis; monthly average of business-day yields. It is a yield, not an ETF price or total return. |
| Units and frequency | Percent per annum, not seasonally adjusted, monthly. 4.99 means 4.99%, not 499% or a 4.99% monthly return. The CSV's first-of-month date labels the month measured. |
| Publication lag | The full monthly average is available after the month ends. In the checked September 2026 case, it was absent September 30 and present October 1: one calendar day after month-end. This example does not establish a fixed lag for every month. |
| Timing limit | H.15 is normally posted on business days at 4:15 p.m.; FRED can update afterward. A vintage date alone does not prove availability before a same-day trade. Use a verified timestamp or trade the following session. |
| Revisions | Zero changed shared observations between the September 30 vintage and today's download, across all downloaded history. That is observed stability, not a guarantee that corrections never occur. Retain vintages. |
| Download date | October 29, 2026. Exact retrieval times, URLs, and saved CSV filenames are in [download_manifest.json](data/download_manifest.json). |
| Missing data | A dot is missing, not zero. Do not forward-fill missing observations into the audit or count them as revisions. |

**Partner attack:** "Publication lag is the field I trust least. Does a September date mean you could use September's average at September month-end?"

**Response:** The app's September 30 vintage ends in August at 4.68%, while today's file adds September at 4.99%, so the September observation date does not establish month-end availability. The [October 1 ALFRED vintage](https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GS10&vintage_date=2026-10-01) contains September's 4.99%, but I would still trade after verified publication rather than assume it was available at the opening.

## I — Implement

**Partner question:** Why not download today's numbers and keep dates before the cutoff?

**Answer:** A measured date says when the event occurred, not when its value was published. That filter would keep later revisions to old observations and could also keep a month whose number had not been released yet.

This is preparation for the required six-minute explanation without AI, not a claim that the partner exercise has happened.

## V — Validate

Run `python3 validate.py` to repeat the live checks. The executed [validation transcript](outputs/validation_run.txt), [comparison CSV](outputs/asof_comparisons.csv), and [visible report](outputs/executed_report.html) retain the results.

### October 5, 2026 known answer

| Series | Last measured date known then | Downloaded value | Later values today | Revised shared dates | Result |
|---|---|---:|---:|---:|---|
| BAA | September 2026 | 6.47% | 0 | 0 | Pass |
| FEDFUNDS | September 2026 | 3.75% | 0 | 0 | Pass |
| DGS10 | October 2, 2026 | 5.28% | 17 | 0 | Pass |
| MORTGAGE30US | October 1, 2026 | 7.28% | 4 | 0 | Pass |

All four are actual ALFRED downloads and match the course known answer. Zero later monthly values is reasonable because the October monthly values are not yet in today's files.

### PAYEMS probe: January 15, 2025

The last known month is **December 2024: 159,536 thousand jobs**. Today's value **for that same December** is **158,316**, lower by **1,220 thousand jobs**. There are **381 revised shared observations** across the downloaded history and **21 later observations**. Today's latest month is September 2026, 159,044; that is a different period and is not the correct comparison for December's revision. The nonzero revision count shows that the app did not download today's data twice. See [payems_revisions.csv](outputs/payems_revisions.csv).

The UI checks also passed: four default charts and rows, default dates, all four historical answers in the rendered table, a typed GS10 ID, isolation of an unknown ID, and an empty selection. Separate small checks confirm that dots remain missing and that later observations and same-date revisions are counted separately.

## E — Evolve: my series

| As known on | Last measured month available | Value | Today's later values | Revised shared dates |
|---|---|---:|---:|---:|
| September 30, 2026 | August 2026 | 4.68% | 1 | 0 |
| October 29, 2026 | September 2026 | 4.99% | 0 | 0 |

September's value vanishes when I move the cutoff back to September 30 because it had not yet been published. The October 1 boundary check confirms its later availability. The displayed change from the latest known 4.68% to 4.99% is **0.31 percentage points**, but it compares two measured months; it is not a revision of August.

## My call

**Admit GS10 conditionally for Project 2.** At each decision cutoff, use only the latest nonmissing monthly value in that date's ALFRED vintage; preserve both the measured month and the cutoff. For a month-end signal acted on at the next opening, use the prior calendar day's vintage so an end-of-day release cannot enter an earlier trade. September 30's signal would therefore use August's 4.68%, not September's 4.99%.

I would quarantine the series if its vintage or publication timing could not be verified, or if a correction changed the input without a reliable historical record. Admitting the data does not establish a useful trading rule; I would freeze a rule before evaluating it and keep the holdout untouched.

## Learn — Data cards

**What is a data card?** A short record of where a series came from, what its values mean, and when I could have used them.

**Which fields prevent leakage?** Publication timing and vintages determine availability; the measured month identifies the period; revisions establish which version belongs in the decision. Units prevent a separate error, such as treating an annual yield as a monthly return. The download date makes the comparison reproducible.

**Why isn't “cleaned the data” enough?** It does not tell another person whether I used information available at the time. A perfectly formatted file can still contain future publications or revised history.

## Reflect

**How late is my series?** In the checked case the monthly number appeared the day after month-end. The app shows that September 30 still had August as the latest month. I should check each cutoff rather than assume every month follows the same schedule.

**What would today's values overstate?** Using September's average to trade during September would give my rule information about yields from days that had not happened yet. A naive backtest could overstate the timeliness of the signal and how well it adjusted bond exposure. This audit does not calculate how much return would be overstated; that requires a specified rule, execution timing, and costs.
