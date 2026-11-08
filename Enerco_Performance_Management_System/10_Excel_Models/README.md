# Excel Models

## Enerco Performance Ranking & Hybrid Bell Curve Calculator

**File:** `Enerco_Performance_Ranking_BellCurve_Calculator.xlsx` (macro-free, Excel 2016 or later)
**Scope:** Enerco only. Capacity: 300 employees and 200 calibration entries.
**Sample data:** 120 synthetic employees. No real data.

| Sheet | Type | Purpose |
|---|---|---|
| Read_Me | Guide | How to use the workbook, and the step-by-step calculation methodology |
| Dashboard | Output | Distribution vs. guideline, rewards by rating, costs by department, top-20 ranking, job-level distribution, 3 charts |
| Config | Input | Every percentage and assumption: weights, KPI caps, proficiency conversion, rating bands, curve rules, bonus multipliers, company scorecard and payout table, budgets, merit matrix, grades and salary ranges |
| Employees | Input | Employee master data (ID, department, job level, grade, dates, salary, eligibility) |
| Performance_Input | Input | 5 KPIs (weight and achievement %), 5 competencies, 4 behaviors, evidence check |
| Ranking_Calc | Formulas | Scores, score-based rating, rank in comparison group, curve rating, hybrid rule, calibration override, final rating, company rank, flags |
| Calibration_Log | Input + controls | Documented exceptions. An entry is applied only when it is Approved, has evidence and has a final approver. |
| Bonus | Formulas | Bonus by employee: base × target % × company factor × multiplier × proration × funding factor |
| Merit | Formulas | Compa-ratio, matrix %, budget scale, new salary, range-max review status |
| Budget_Control | Formulas | Bonus and merit budget vs. cost, funding factor, scale-to-fit, 2/3/4%/custom simulation |
| Group_Analysis | Formulas | Distribution by job level, grade and department, with tolerance flags |
| Checks | Formulas | 18 integrity checks and an overall status |
| Audit_Trail | Input | Change and approval log with control totals |

### How the hybrid bell curve works
1. Each employee gets a **score-based rating** from the rating bands.
2. Within the **comparison group** (Job Level by default, or Grade), employees are ranked. The guideline 5/15/60/15/5 gives a **curve rating** by rank.
3. **Hybrid rule:** the curve can move the rating by at most 1 level (configurable). Groups smaller than 10 (configurable) are not curved.
4. **Curve reductions are not applied automatically.** They wait for committee confirmation in Calibration_Log, in line with the approved principle of no automatic downgrades. **Curve uplifts are applied automatically by default.** Set `CONFIRM_UP = Yes` on Config to make uplifts wait for the committee too.
5. Approved calibration entries override everything. Bonus and merit always use the **final** rating.

### Rebuild and verify
```bash
python build_ranking_calculator.py      # writes the .xlsx (openpyxl)
python verify_ranking_calculator.py     # LibreOffice recalculation + independent Python check
```
The latest verification result is in `19_Testing/Excel_Ranking_Calculator_Verification.md`.
