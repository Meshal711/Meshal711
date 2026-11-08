# Excel Ranking & Bell Curve Calculator – Verification Report

**Workbook:** `10_Excel_Models/Enerco_Performance_Ranking_BellCurve_Calculator.xlsx`  
**Run:** 2026-11-08 · recalculated with LibreOffice Calc (headless) · compared with an independent Python implementation (`verify_ranking_calculator.py`) that reads only the input cells.  
**Employees checked:** 120 (synthetic) · **Fields compared per employee:** 12 · **Comparisons:** 1440

## Result

- Mismatches between Excel and independent calculation: **0**
- Excel error values (#N/A, #VALUE!, #REF!, #NAME?, #DIV/0!, …) in any sheet: **0**
- Company score 99.9 → company factor Excel 0.999 / Python 0.999
- Model checks overall status (Checks sheet): **REVIEW**


## Dashboard snapshot (sample data, default configuration)

| Rating | Guideline % | Score-based # | Final # | Final % |
|---|---|---|---|---|
| 5 – Exceptional | 5% | 1 | 6 | 5.0% |
| 4 – Exceeds Expectations | 15% | 29 | 26 | 21.7% |
| 3 – Meets Expectations | 60% | 77 | 76 | 63.3% |
| 2 – Partially Meets Expectations | 15% | 12 | 11 | 9.2% |
| 1 – Does Not Meet Expectations | 5% | 1 | 1 | 0.8% |

| Budget item | Value |
|---|---|
| Bonus budget (SAR) | 2,600,000 |
| Target bonus pool – eligible employees (SAR) | 2,468,954 |
| Calculated bonus liability before funding factor (SAR) | 2,521,841 |
| Funding factor applied | 1 |
| Final bonus payout (SAR) | 2,521,841 |
| Remaining budget (SAR) | 78,159 |
| Budget utilisation | 0.9699 |
| Payout as % of target pool | 1.0214 |
| Bonus budget status | Within budget |
| Eligible annual base payroll (SAR) | 19,450,800 |
| Merit budget % | 0.0300 |
| Merit budget (SAR, annual) | 583,524 |
| Matrix cost before scaling (SAR, annual) | 401,075 |
| Scale factor that would fit the budget | 1.4549 |
| Budget scale applied | 1 |
| Final merit cost (SAR, annual) | 401,075 |
| Final merit cost as % of eligible payroll | 0.0206 |
| Variance vs budget (SAR; + = under budget) | 182,449 |
| Employees receiving an increase | 93 |
| Eligible employees with no increase | 24 |
| Cases flagged for range-max review | 4 |
| Merit budget status | Within budget |

## Checks sheet

| # | Check | Result | Status |
|---|---|---|---|
| 1 | Performance weights total 100% | 1 | PASS |
| 2 | Guideline distribution totals 100% | 1 | PASS |
| 3 | Rating band lower bounds ascending | OK | PASS |
| 4 | Company scorecard weights total 100% | 1 | PASS |
| 5 | Employees loaded | 120 | PASS |
| 6 | Duplicate Employee IDs | 0 | PASS |
| 7 | Grades not found in salary range table | 0 | PASS |
| 8 | Missing salary or hire date | 0 | PASS |
| 9 | Employees whose KPI weights do not total 100% | 0 | PASS |
| 10 | Employees with missing competency/behavior ratings | 1 | WARN |
| 11 | Final ratings outside 1–5 | 0 | PASS |
| 12 | Curve changes awaiting committee | 24 | WARN |
| 13 | Calibration entries Approved but not applied (missing evidence/approver/ID) | 0 | PASS |
| 14 | Bonus total reconciles with Dashboard | 0 | PASS |
| 15 | Bonus payout within budget | Within budget | PASS |
| 16 | Merit cost within budget | Within budget | PASS |
| 17 | Merit cases needing range-max review | 4 | WARN |
| 18 | Formula errors in calculation sheets | 0 | PASS |

WARN items are expected with the sample data: they show the controls working (a missing rating, curve reductions awaiting committee confirmation, range-max review cases, bonus budget pressure).

## Configuration scenarios (each recalculated in LibreOffice and re-verified independently)

| Scenario | Comparisons | Mismatches | Errors | Final 5/4/3/2/1 | Company factor | Funding factor | Merit scale | Bonus (SAR) | Merit (SAR/yr) |
|---|---|---|---|---|---|---|---|---|---|
| Forced curve, Grade comparison groups | 1080 | 0 | 0 | 7/26/74/12/1 | 0.999 | 1.0000 | 1.0000 | 2,444,564 | 392,785 |
| Guided mode (score bands only) | 1080 | 0 | 0 | 1/30/76/12/1 | 0.999 | 1.0000 | 1.0000 | 2,418,466 | 375,300 |
| Hybrid, all curve changes auto-applied, max adjustment 2 | 1080 | 0 | 0 | 6/19/71/18/6 | 0.999 | 1.0000 | 1.0000 | 2,338,488 | 350,573 |
| Approved alternative bands 110/100/85/70 | 1080 | 0 | 0 | 8/48/58/6/0 | 0.999 | 1.0000 | 1.0000 | 2,666,090 | 473,653 |
| Step payout, weak company year (score ~78) | 1080 | 0 | 0 | 6/26/76/11/1 | 0.5 | 1.0000 | 1.0000 | 1,262,182 | 401,075 |
| Bonus budget 1.5M with funding factor; merit scaled to 4% budget | 1080 | 0 | 0 | 6/26/76/11/1 | 0.999 | 0.5948 | 1.9399 | 1,500,000 | 758,994 |
| Weights 60/30/10, min group 20 | 1080 | 0 | 0 | 4/26/70/19/1 | 0.999 | 1.0000 | 1.0000 | 2,303,884 | 350,652 |
