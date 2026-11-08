"""Builds Enerco_Performance_Ranking_BellCurve_Calculator.xlsx.

Every calculation in the workbook is a live Excel formula; this script only lays
out the sheets, writes formulas, styles, validation and the synthetic sample data.

Run:  python build_ranking_calculator.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).with_name("Enerco_Performance_Ranking_BellCurve_Calculator.xlsx")
FIRST, LAST = 5, 304            # employee data rows (capacity 300)
LOG_FIRST, LOG_LAST = 5, 204    # calibration log rows (capacity 200)
AUD_FIRST, AUD_LAST = 5, 504

# ---------------------------------------------------------------- styles
NAVY = "1F3A5F"
TEAL = "2E7D7A"
F_TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY)
F_SUB = Font(name="Calibri", size=10, italic=True, color="595959")
F_HEAD = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
F_SECTION = Font(name="Calibri", size=12, bold=True, color=TEAL)
F_BOLD = Font(bold=True)
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_INPUT = PatternFill("solid", fgColor="FFF2CC")
FILL_CALC = PatternFill("solid", fgColor="F2F2F2")
FILL_KEY = PatternFill("solid", fgColor="DDEBF7")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
UNLOCK = Protection(locked=False)

wb = Workbook()
names = {}


def define(name, ref):
    wb.defined_names[name] = DefinedName(name=name, attr_text=ref)
    names[name] = ref


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = F_TITLE
    ws["A2"] = sub
    ws["A2"].font = F_SUB


def header(ws, row, headers, widths=None):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font, c.fill, c.alignment, c.border = F_HEAD, FILL_HEAD, CENTER, BORDER
    ws.row_dimensions[row].height = 42
    if widths:
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w


def style_input(c, fmt=None):
    c.fill, c.border, c.protection = FILL_INPUT, BORDER, UNLOCK
    if fmt:
        c.number_format = fmt


def style_calc(c, fmt=None):
    c.fill, c.border = FILL_CALC, BORDER
    if fmt:
        c.number_format = fmt


def protect(ws):
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    ws.protection.autoFilter = False
    ws.protection.sort = False


def add_list_validation(ws, rng, source, prompt=None):
    dv = DataValidation(type="list", formula1=source, allow_blank=True, showErrorMessage=True,
                        errorTitle="Invalid value", error="Choose a value from the list.")
    if prompt:
        dv.promptTitle, dv.prompt, dv.showInputMessage = "Input", prompt, True
    ws.add_data_validation(dv)
    dv.add(rng)


def add_num_validation(ws, rng, lo, hi, whole=False, msg=None):
    dv = DataValidation(type="whole" if whole else "decimal", operator="between", formula1=str(lo),
                        formula2=str(hi), allow_blank=True, showErrorMessage=True,
                        errorTitle="Out of range", error=msg or f"Enter a value between {lo} and {hi}.")
    ws.add_data_validation(dv)
    dv.add(rng)


# =====================================================================
# Lists (hidden dropdown sources)
# =====================================================================
ws_lists = wb.active
ws_lists.title = "Lists"
LISTS = {
    "YesNo": ["Yes", "No"],
    "CurveMode": ["Hybrid", "Guided", "Forced"],
    "Basis": ["Job Level", "Grade"],
    "PayMethod": ["Linear", "Step"],
    "Reason": ["Evidence not reflected in score", "KPI data corrected", "Target set incorrectly (verified)",
               "Curve adjustment confirmed", "Curve adjustment reversed", "Manager rating inconsistency",
               "Exceptional contribution outside KPIs", "Other (explain in evidence)"],
    "HRReview": ["Supported", "Not supported", "Pending"],
    "Decision": ["Approved", "Rejected", "Pending"],
    "JobLevel": ["Individual Contributor", "Supervisor", "Manager", "Senior Management"],
    "Department": ["Operations", "Engineering", "Projects", "Finance", "Human Resources",
                   "Supply Chain", "HSE", "Commercial"],
}
for col, (key, vals) in enumerate(LISTS.items(), start=1):
    ws_lists.cell(row=1, column=col, value=key).font = F_BOLD
    for r, v in enumerate(vals, start=2):
        ws_lists.cell(row=r, column=col, value=v)
    L = get_column_letter(col)
    define(f"L_{key}", f"Lists!${L}$2:${L}${len(vals) + 1}")
ws_lists.sheet_state = "hidden"

# =====================================================================
# README / Methodology
# =====================================================================
ws_m = wb.create_sheet("Read_Me", 0)
title(ws_m, "Enerco Performance Ranking & Hybrid Bell Curve Calculator",
      "Enerco only · Version 1.0 · Sample data is synthetic (no real employees) · All percentages are configurable on the Config sheet")
ws_m.column_dimensions["A"].width = 4
ws_m.column_dimensions["B"].width = 34
ws_m.column_dimensions["C"].width = 120
METHOD = [
    ("HOW TO USE", None),
    ("1. Config", "Set weights, rating bands, distribution, curve rules, bonus multipliers, company factor, merit matrix, salary ranges and budgets. Yellow cells are inputs; grey cells are formulas."),
    ("2. Employees", "Paste or type one row per employee (up to 300). Use Employee IDs; names are optional."),
    ("3. Performance_Input", "Enter up to 5 KPIs (weight + achievement %), 5 competency ratings and 4 behavior ratings (1–5) per employee, and whether KPI evidence was verified."),
    ("4. Ranking_Calc", "Fully automatic: scores, rating, rank within comparison group, bell-curve rating, hybrid rating, final rating and flags."),
    ("5. Calibration_Log", "Committee records every exception. An exception changes the final rating only when Decision = Approved AND evidence AND final approver are filled in."),
    ("6. Bonus / Merit / Budget_Control", "Automatic reward calculations from the FINAL rating, with budget checks and optional funding factor / matrix scaling."),
    ("7. Dashboard", "Management view: distribution vs guideline, rankings, bonus and merit costs, check status."),
    ("8. Checks", "Must show ALL PASS before results are released. Audit_Trail: log every change to Config, data and approvals."),
    ("", None),
    ("CALCULATION METHODOLOGY", None),
    ("Step 1 – KPI score", "Each KPI score = achievement % × 100, capped at the KPI maximum (default 120). If KPI evidence is not verified, the cap is 100 (no credit above target without evidence). KPI Score = Σ(weight × KPI score) ÷ Σ weights. Weights should total 100% (flagged if not)."),
    ("Step 2 – Competency & behavior", "Each 1–5 rating is converted to the common 0–120 scale using the proficiency table (default 1=60, 2=80, 3=100, 4=110, 5=120). Competency Score and Behavior Score = average of converted ratings."),
    ("Step 3 – Final score", "Final Score = KPI × 70% + Competency × 20% + Behavior × 10% (weights configurable), rounded to 2 decimals. All components use the same scale, so 100 = fully meets expectations."),
    ("Step 4 – Score-based rating", "Final Score is placed in the rating bands (lower bound inclusive). Default bands = 'Option A' recommended in Phase 1 (5 ≥115, 4 ≥105, 3 ≥90, 2 ≥75, 1 <75). The approved alternative (110/100/85/70) can be typed into the Config band table."),
    ("Step 5 – Comparison group & rank", "Employees are compared only within their comparison group: Job Level (default) or Grade (Config). Rank 1 = highest final score in the group; ties are broken by row order and flagged by identical scores."),
    ("Step 6 – Bell curve rating", "Within each group of size n, the top ROUND(n×5%) are curve-rated 5, the next up to ROUND(n×20%) are 4, up to ROUND(n×80%) are 3, up to ROUND(n×95%) are 2, the rest 1 (percentages from Config). Groups smaller than the minimum size are not curved."),
    ("Step 7 – Hybrid rule", "Hybrid mode: the curve may move a rating by at most the 'maximum curve adjustment' (default 1 level) from the score-based rating. By default curve reductions are NOT applied automatically – they wait for committee confirmation in the Calibration_Log (Config switch). Guided mode = score-based rating only (curve shown for reference). Forced mode = pure curve (comparison only, not recommended)."),
    ("Step 8 – Calibration", "An approved Calibration_Log entry overrides the system rating. The preliminary score, score-based rating, curve rating and final rating are all kept side by side."),
    ("Step 9 – Annual bonus", "Bonus = Monthly Basic × Bonus months (12) × Target Bonus % (by grade) × Company Performance Factor × Individual Multiplier (by final rating) × Proration. Proration = eligible days in the cycle (net of unpaid leave) ÷ cycle days; 0 below the minimum service days. If the bonus budget is exceeded and 'Apply funding factor' = Yes, every bonus is multiplied by Budget ÷ Liability. Ratings are never changed to fit the budget."),
    ("Step 10 – Merit increase", "Compa-Ratio = Monthly Basic ÷ Range Midpoint × 100. Merit % = Merit Matrix (final rating × compa-ratio band) × budget scale, capped at the maximum merit %. If 'Scale matrix to budget' = Yes the whole matrix is scaled uniformly so total cost equals the merit budget. Increases that would exceed the range maximum are flagged for review, not truncated."),
    ("", None),
    ("IMPORTANT NOTES", None),
    ("Status of percentages", "All multipliers, matrix values, target bonus % and salary ranges in this file are ILLUSTRATIVE assumptions for simulation. They are not approved Enerco pay decisions."),
    ("Legal", "Bonus eligibility for leavers and the legal character of the bonus (Saudi Labor Law, Article 2 wage definitions) must be validated by Legal before payout. Leaver bonuses are flagged in the Bonus sheet."),
    ("Protection", "Formula sheets are protected without a password to prevent accidental edits (Review > Unprotect Sheet). Record any unprotect/change in the Audit_Trail."),
    ("Not included", "This is a calculator, not an HR system: there is no automatic workflow, e-mail or user login. Approvals are recorded in the Calibration_Log and Audit_Trail."),
]
r = 4
for k, v in METHOD:
    if v is None:
        ws_m.cell(row=r, column=2, value=k).font = F_SECTION
    else:
        ws_m.cell(row=r, column=2, value=k).font = F_BOLD
        c = ws_m.cell(row=r, column=3, value=v)
        c.alignment = WRAP
        ws_m.row_dimensions[r].height = max(15, 15 * (len(v) // 115 + 1))
    r += 1

# =====================================================================
# Config
# =====================================================================
ws_c = wb.create_sheet("Config", 1)
title(ws_c, "Configuration – all assumptions and percentages",
      "Yellow = input. Changing a value here recalculates the whole model. Log every change in Audit_Trail.")
for col, w in zip("ABCDEFGH", (38, 22, 16, 16, 16, 16, 16, 60)):
    ws_c.column_dimensions[col].width = w

row = 4


def section(text):
    global row
    row += 1
    ws_c.cell(row=row, column=1, value=text).font = F_SECTION
    row += 1


def param(name, label, value, note="", fmt=None, listsrc=None, rng=None):
    global row
    ws_c.cell(row=row, column=1, value=label).border = BORDER
    c = ws_c.cell(row=row, column=2, value=value)
    style_input(c, fmt)
    ws_c.cell(row=row, column=8, value=note).alignment = WRAP
    if listsrc:
        add_list_validation(ws_c, f"B{row}", listsrc)
    if rng:
        add_num_validation(ws_c, f"B{row}", *rng)
    define(name, f"Config!$B${row}")
    row += 1


def calc_param(name, label, formula, note="", fmt=None):
    global row
    ws_c.cell(row=row, column=1, value=label).border = BORDER
    c = ws_c.cell(row=row, column=2, value=formula)
    style_calc(c, fmt)
    c.font = F_BOLD
    ws_c.cell(row=row, column=8, value=note).alignment = WRAP
    define(name, f"Config!$B${row}")
    row += 1


section("A. Cycle")
param("CYCLE_YEAR", "Performance cycle year", 2026, "", "0")
param("CYCLE_START", "Cycle start date", date(2026, 1, 1), "", "dd-mmm-yyyy")
param("CYCLE_END", "Cycle end date", date(2026, 12, 31), "", "dd-mmm-yyyy")

section("B. Performance weights (must total 100%)")
param("W_KPI", "KPIs & individual objectives", 0.70, "Approved: 70%", "0%", rng=(0, 1))
param("W_COMP", "Core & functional competencies", 0.20, "Approved: 20%", "0%", rng=(0, 1))
param("W_BEH", "Corporate values & behaviors", 0.10, "Approved: 10%", "0%", rng=(0, 1))
calc_param("W_TOTAL", "Total (check)", "=W_KPI+W_COMP+W_BEH", "Must equal 100% (see Checks)", "0%")

section("C. KPI scoring controls")
param("KPI_MAX", "Maximum KPI score (score cap)", 120, "Achievement above 120% earns no further credit", "0", rng=(100, 200))
param("KPI_CAP_NOEVID", "KPI cap when evidence NOT verified", 100, "No credit above target without verified evidence", "0", rng=(0, 200))

section("D. Proficiency conversion (1–5 rating → 0–120 scale)")
for i, h in enumerate(["Level", "1", "2", "3", "4", "5"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
ws_c.cell(row=row, column=1, value="Score on common scale")
for i, v in enumerate([60, 80, 100, 110, 120], start=2):
    style_input(ws_c.cell(row=row, column=i, value=v), "0")
define("PROF_SCORES", f"Config!$B${row}:$F${row}")
ws_c.cell(row=row, column=8, value="Level 3 (fully proficient) = 100 = same meaning as a KPI on target")
row += 1

section("E. Rating bands (score after rounding to 2 dp; lower bound inclusive; ascending)")
for i, h in enumerate(["Rating", "Label", "Lower bound", "Approved alt.", "", "", "", "Definition"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
band_start = row
BANDS = [(1, "Does Not Meet Expectations", 0, 0, "Results and behaviors clearly below the standard of the role."),
         (2, "Partially Meets Expectations", 75, 70, "Meets some but not all expectations; improvement needed."),
         (3, "Meets Expectations", 90, 85, "Fully delivers the role's objectives and expected behaviors."),
         (4, "Exceeds Expectations", 105, 100, "Delivers above target on most objectives with strong behaviors."),
         (5, "Exceptional", 115, 110, "Outstanding results well beyond target; a role model.")]
for rt, lab, lo, alt, desc in BANDS:
    ws_c.cell(row=row, column=1, value=rt).border = BORDER
    style_input(ws_c.cell(row=row, column=2, value=lab))
    style_input(ws_c.cell(row=row, column=3, value=lo), "0.00")
    ws_c.cell(row=row, column=4, value=alt).number_format = "0.00"
    ws_c.cell(row=row, column=8, value=desc).alignment = WRAP
    row += 1
define("BAND_RATING", f"Config!$A${band_start}:$A${row - 1}")
define("BAND_LABEL", f"Config!$B${band_start}:$B${row - 1}")
define("BAND_LOWER", f"Config!$C${band_start}:$C${row - 1}")
ws_c.cell(row=row, column=1, value="Note: 'Approved alt.' shows the approved table (110/100/85/70). Phase 1 found that with it, meeting every target (score 100) is rated 'Exceeds'. Decision D-07 pending – copy column D into C to use it.").alignment = WRAP
ws_c.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
ws_c.row_dimensions[row].height = 30
row += 1

section("F. Hybrid bell curve")
for i, h in enumerate(["Rating", "Label", "Guideline %"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
dist_rows = {}
for rt, pctv in ((5, 0.05), (4, 0.15), (3, 0.60), (2, 0.15), (1, 0.05)):
    ws_c.cell(row=row, column=1, value=rt).border = BORDER
    ws_c.cell(row=row, column=2, value=f"=INDEX(BAND_LABEL,{rt})").border = BORDER
    style_input(ws_c.cell(row=row, column=3, value=pctv), "0.0%")
    define(f"DIST_{rt}", f"Config!$C${row}")
    dist_rows[rt] = row
    row += 1
ws_c.cell(row=row, column=1, value="Total (must be 100%)")
c = ws_c.cell(row=row, column=3, value="=SUM(DIST_1,DIST_2,DIST_3,DIST_4,DIST_5)")
style_calc(c, "0.0%")
define("DIST_TOTAL", f"Config!$C${row}")
row += 2
param("CURVE_MODE", "Curve mode", "Hybrid", "Hybrid = curve within ± max adjustment; Guided = score bands only (curve for reference); Forced = pure curve (not recommended)", listsrc="=L_CurveMode")
param("COMP_BASIS", "Comparison group basis", "Job Level", "Employees are ranked and curved only against peers in the same Job Level or Grade", listsrc="=L_Basis")
param("MIN_GROUP", "Minimum group size to apply curve", 10, "Smaller groups keep score-based ratings (too small for a distribution)", "0", rng=(1, 500))
param("MAX_ADJ", "Maximum curve adjustment (levels)", 1, "Hybrid mode only: how far the curve may move a rating from the score-based rating", "0", rng=(0, 4))
param("CONFIRM_DOWN", "Curve reductions need committee confirmation", "Yes", "Yes = a curve reduction is NOT applied until approved in Calibration_Log (no automatic downgrade)", listsrc="=L_YesNo")
param("CONFIRM_UP", "Curve uplifts need committee confirmation", "No", "Yes = uplifts also wait for the committee", listsrc="=L_YesNo")
param("DIST_TOL", "Distribution variance tolerance (pp)", 0.10, "Group_Analysis flags a rating whose share differs from guideline by more than this", "0%", rng=(0, 1))

section("G. Annual bonus")
param("BONUS_MONTHS", "Salary months in bonus base", 12, "12 × monthly basic = annual basic salary (allowances excluded)", "0", rng=(0, 24))
for i, h in enumerate(["Rating", "Label", "Multiplier"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
mult_start = row
for rt, m in ((1, 0.0), (2, 0.5), (3, 1.0), (4, 1.25), (5, 1.5)):
    ws_c.cell(row=row, column=1, value=rt).border = BORDER
    ws_c.cell(row=row, column=2, value=f"=INDEX(BAND_LABEL,{rt})").border = BORDER
    style_input(ws_c.cell(row=row, column=3, value=m), "0.00")
    row += 1
define("BONUS_MULT", f"Config!$C${mult_start}:$C${row - 1}")
row += 1
for i, h in enumerate(["Company scorecard component", "Weight", "Score (0–120)"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
cs_start = row
for comp, w, s in (("Financial performance", 0.5, 98), ("Operational performance", 0.3, 103), ("Strategic objectives", 0.2, 100)):
    ws_c.cell(row=row, column=1, value=comp).border = BORDER
    style_input(ws_c.cell(row=row, column=2, value=w), "0%")
    style_input(ws_c.cell(row=row, column=3, value=s), "0.0")
    row += 1
define("CS_WEIGHTS", f"Config!$B${cs_start}:$B${row - 1}")
define("CS_SCORES", f"Config!$C${cs_start}:$C${row - 1}")
calc_param("COMPANY_SCORE", "Company performance score", "=ROUND(SUMPRODUCT(CS_WEIGHTS,CS_SCORES),2)", "Weighted company scorecard result (approved by Executive Management)", "0.00")
param("PAY_METHOD", "Company payout method", "Linear", "Step = table value; Linear = interpolate between table points (removes cliffs)", listsrc="=L_PayMethod")
for i, h in enumerate(["Company score from", "Payout factor"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
pay_start = row
for thr, fac in ((0, 0.0), (70, 0.5), (80, 0.75), (90, 0.9), (100, 1.0), (110, 1.2)):
    style_input(ws_c.cell(row=row, column=1, value=thr), "0.00")
    style_input(ws_c.cell(row=row, column=2, value=fac), "0.00")
    row += 1
define("PAY_THR", f"Config!$A${pay_start}:$A${row - 1}")
define("PAY_FAC", f"Config!$B${pay_start}:$B${row - 1}")
calc_param("CPF", "Company Performance Factor (applied)",
           "=IF(PAY_METHOD=\"Step\",LOOKUP(COMPANY_SCORE,PAY_THR,PAY_FAC),"
           "IF(COMPANY_SCORE<INDEX(PAY_THR,2),0,IF(COMPANY_SCORE>=INDEX(PAY_THR,COUNT(PAY_THR)),INDEX(PAY_FAC,COUNT(PAY_FAC)),"
           "ROUND(INDEX(PAY_FAC,MATCH(COMPANY_SCORE,PAY_THR,1))+(INDEX(PAY_FAC,MATCH(COMPANY_SCORE,PAY_THR,1)+1)-INDEX(PAY_FAC,MATCH(COMPANY_SCORE,PAY_THR,1)))"
           "*(COMPANY_SCORE-INDEX(PAY_THR,MATCH(COMPANY_SCORE,PAY_THR,1)))/(INDEX(PAY_THR,MATCH(COMPANY_SCORE,PAY_THR,1)+1)-INDEX(PAY_THR,MATCH(COMPANY_SCORE,PAY_THR,1))),4))))",
           "Below the second table row the factor is 0; at or above the last row it is capped", "0.0000")
param("MIN_SERVICE", "Minimum eligible service days for bonus", 90, "PROPOSED – requires legal validation", "0", rng=(0, 366))
param("BONUS_BUDGET", "Total bonus budget (SAR)", 2_600_000, "Approved by Executive Management / Finance", "#,##0", rng=(0, 1e12))
param("APPLY_FF", "Apply funding factor if budget exceeded", "No", "Yes = all bonuses scaled down uniformly to fit budget (executive decision; ratings unchanged)", listsrc="=L_YesNo")

section("H. Merit increase")
param("MERIT_BUDGET_PCT", "Merit budget (% of eligible annual base payroll)", 0.03, "Simulate 2%, 3%, 4% or custom", "0.0%", rng=(0, 1))
param("SCALE_TO_BUDGET", "Scale matrix to budget", "No", "Yes = every matrix cell multiplied by the same factor so total cost = budget", listsrc="=L_YesNo")
param("MERIT_MAX", "Maximum merit increase per employee", 0.10, "", "0.0%", rng=(0, 1))
param("MERIT_CUTOFF", "Merit eligibility: hired before", date(2026, 10, 1), "Employees hired on/after this date are not eligible this cycle", "dd-mmm-yyyy")
param("MERIT_CUSTOM", "Custom budget % for simulation", 0.035, "", "0.0%", rng=(0, 1))
row += 1
ws_c.cell(row=row, column=1, value="Merit matrix (illustrative – NOT approved increases)").font = F_BOLD
row += 1
ws_c.cell(row=row, column=1, value="Compa-ratio band lower bound (%)").font = F_BOLD
for i, v in enumerate([0, 80, 90, 100, 110], start=2):
    style_input(ws_c.cell(row=row, column=i, value=v), "0")
define("CR_LOWER", f"Config!$B${row}:$F${row}")
row += 1
ws_c.cell(row=row, column=1, value="Band label").font = F_BOLD
for i, v in enumerate(["Below 80%", "80–89.99%", "90–99.99%", "100–109.99%", "110%+"], start=2):
    style_calc(ws_c.cell(row=row, column=i, value=v))
define("CR_LABELS", f"Config!$B${row}:$F${row}")
row += 1
mm_start = row
MATRIX = {5: [0.08, 0.07, 0.06, 0.04, 0.02], 4: [0.06, 0.05, 0.04, 0.03, 0.01],
          3: [0.04, 0.03, 0.02, 0.015, 0.0], 2: [0, 0, 0, 0, 0], 1: [0, 0, 0, 0, 0]}
for rt in (5, 4, 3, 2, 1):
    ws_c.cell(row=row, column=1, value=f"=\"{rt} – \"&INDEX(BAND_LABEL,{rt})").border = BORDER
    for i, v in enumerate(MATRIX[rt], start=2):
        style_input(ws_c.cell(row=row, column=i, value=v), "0.0%")
    row += 1
define("MERIT_MATRIX", f"Config!$B${mm_start}:$F${row - 1}")
ws_c.cell(row=mm_start, column=8, value="Rows: final rating 5 (top) to 1. Columns: compa-ratio band.")

section("I. Grades and salary ranges (monthly basic, SAR – ILLUSTRATIVE)")
for i, h in enumerate(["Grade", "Job Level", "Range Min", "Range Mid", "Range Max", "Target Bonus %"], start=1):
    ws_c.cell(row=row, column=i, value=h).font = F_BOLD
row += 1
GRADES = [("G05", "Individual Contributor", 6500, 0.05), ("G06", "Individual Contributor", 8000, 0.06),
          ("G07", "Individual Contributor", 9800, 0.08), ("G08", "Individual Contributor", 12000, 0.10),
          ("G09", "Supervisor", 14700, 0.10), ("G10", "Manager", 18000, 0.12),
          ("G11", "Manager", 22000, 0.15), ("G12", "Senior Management", 27000, 0.20),
          ("G13", "Senior Management", 33000, 0.25)]
gr_start = row
for g, lvl, mid, tgt in GRADES:
    style_input(ws_c.cell(row=row, column=1, value=g))
    style_input(ws_c.cell(row=row, column=2, value=lvl))
    style_input(ws_c.cell(row=row, column=3, value=round(mid / 1.2, 0)), "#,##0")
    style_input(ws_c.cell(row=row, column=4, value=mid), "#,##0")
    style_input(ws_c.cell(row=row, column=5, value=round(mid * 1.4 / 1.2, 0)), "#,##0")
    style_input(ws_c.cell(row=row, column=6, value=tgt), "0%")
    row += 1
for _ in range(3):  # spare rows for new grades
    for col in range(1, 7):
        style_input(ws_c.cell(row=row, column=col))
    row += 1
define("GRADE_LIST", f"Config!$A${gr_start}:$A${row - 1}")
define("GRADE_MIN", f"Config!$C${gr_start}:$C${row - 1}")
define("GRADE_MID", f"Config!$D${gr_start}:$D${row - 1}")
define("GRADE_MAX", f"Config!$E${gr_start}:$E${row - 1}")
define("GRADE_TGT", f"Config!$F${gr_start}:$F${row - 1}")
ws_c.freeze_panes = "A4"
protect(ws_c)

# =====================================================================
# Sample data (synthetic)
# =====================================================================
rng = random.Random(2026)
LEVEL_OF = {g: lvl for g, lvl, _, _ in GRADES}
MID_OF = {g: mid for g, _, mid, _ in GRADES}
FAMILY = {"Operations": ["Operations", "Maintenance"], "Engineering": ["Engineering"],
          "Projects": ["Project Management"], "Finance": ["Finance"], "Human Resources": ["Human Resources"],
          "Supply Chain": ["Supply Chain"], "HSE": ["HSE"], "Commercial": ["Commercial"]}
TITLES = {"Individual Contributor": ["Specialist", "Engineer", "Analyst", "Technician", "Officer"],
          "Supervisor": ["Supervisor"], "Manager": ["Manager"], "Senior Management": ["Director", "General Manager"]}
grade_w = [10, 16, 18, 16, 12, 10, 8, 6, 4]
employees, perf = [], []
for i in range(120):
    dept = rng.choices(LISTS["Department"], [22, 18, 14, 10, 6, 10, 8, 12])[0]
    grade = rng.choices([g[0] for g in GRADES], grade_w)[0]
    lvl = LEVEL_OF[grade]
    fam = rng.choice(FAMILY[dept])
    title_txt = f"{fam} {rng.choice(TITLES[lvl])}"
    hire = date(2014, 1, 1) + timedelta(days=rng.randint(0, 11 * 365))
    basic = round(MID_OF[grade] * rng.uniform(0.82, 1.18), -1)
    employees.append({"id": f"EN{1001 + i}", "name": f"Employee {i + 1:03d}", "dept": dept, "family": fam,
                      "title": title_txt, "level": lvl, "grade": grade, "hire": hire, "exit": None,
                      "unpaid": 0, "basic": basic, "bonus_el": "Yes", "merit_el": "Yes"})
    ability = rng.gauss(0, 1)
    kpis = []
    n_k = rng.randint(3, 5)
    ws_raw = [rng.uniform(0.6, 1.4) for _ in range(n_k)]
    tot = sum(ws_raw)
    wts = [round(w / tot, 2) for w in ws_raw]
    wts[-1] = round(1 - sum(wts[:-1]), 2)
    for k in range(n_k):
        ach = max(0.4, round(1 + ability * 0.05 + rng.gauss(0, 0.04), 3))
        kpis.append((wts[k], ach))
    lvl_from = lambda a: int(min(5, max(1, round(3 + a * 0.8 + rng.gauss(0, 0.45)))))
    perf.append({"kpis": kpis, "comp": [lvl_from(ability) for _ in range(5)],
                 "beh": [lvl_from(ability * 0.6) for _ in range(4)], "evid": "Yes"})

# Edge cases
employees[2].update(hire=date(2026, 3, 15))                       # new joiner, prorated
employees[6].update(hire=date(2026, 11, 1))                       # below min service, after merit cut-off
employees[10].update(exit=date(2026, 8, 31))                      # leaver
employees[14].update(unpaid=45)                                   # unpaid leave
employees[18].update(basic=round(MID_OF[employees[18]["grade"]] * 1.4 / 1.2 * 1.03, -1))   # above range max
employees[22].update(basic=round(MID_OF[employees[22]["grade"]] / 1.2 * 0.92, -1))         # below range min
employees[26].update(bonus_el="No")                               # contractually not eligible
employees[30].update(merit_el="No")
perf[34]["evid"] = "No"                                           # unverified KPI evidence
perf[38]["comp"][4] = None                                        # missing competency rating

# =====================================================================
# Employees
# =====================================================================
ws_e = wb.create_sheet("Employees")
title(ws_e, "Employee master data (Enerco)", "Input sheet · up to 300 employees · synthetic sample data")
EMP_HEAD = ["Employee ID", "Employee Name", "Department", "Job Family", "Position Title", "Job Level", "Grade",
            "Hire Date", "Exit Date (if leaver)", "Unpaid Leave Days (cycle)", "Monthly Basic Salary (SAR)",
            "Bonus Eligible", "Merit Eligible"]
header(ws_e, 4, EMP_HEAD, [13, 16, 17, 18, 26, 20, 8, 12, 12, 11, 14, 9, 9])
for idx in range(FIRST, LAST + 1):
    e = employees[idx - FIRST] if idx - FIRST < len(employees) else None
    vals = ([e["id"], e["name"], e["dept"], e["family"], e["title"], e["level"], e["grade"], e["hire"], e["exit"],
             e["unpaid"], e["basic"], e["bonus_el"], e["merit_el"]] if e else [None] * 13)
    for col, v in enumerate(vals, start=1):
        c = ws_e.cell(row=idx, column=col, value=v)
        style_input(c, {8: "dd-mmm-yyyy", 9: "dd-mmm-yyyy", 11: "#,##0"}.get(col))
rngE = f"{FIRST}:{LAST}"
add_list_validation(ws_e, f"C{FIRST}:C{LAST}", "=L_Department")
add_list_validation(ws_e, f"F{FIRST}:F{LAST}", "=L_JobLevel")
add_list_validation(ws_e, f"G{FIRST}:G{LAST}", "=GRADE_LIST")
add_list_validation(ws_e, f"L{FIRST}:M{LAST}", "=L_YesNo")
add_num_validation(ws_e, f"J{FIRST}:J{LAST}", 0, 366, whole=True)
add_num_validation(ws_e, f"K{FIRST}:K{LAST}", 0, 1_000_000)
ws_e.freeze_panes = "B5"
ws_e.auto_filter.ref = f"A4:M{LAST}"

# =====================================================================
# Performance_Input
# =====================================================================
ws_p = wb.create_sheet("Performance_Input")
title(ws_p, "Performance inputs", "KPI weights & achievement (100% = target met) · competency & behavior ratings 1–5 · evidence check")
P_HEAD = ["Employee ID", "Job Level"]
for k in range(1, 6):
    P_HEAD += [f"KPI {k} Weight", f"KPI {k} Achievement %"]
P_HEAD += [f"Competency {k} (1–5)" for k in range(1, 6)] + [f"Behavior {k} (1–5)" for k in range(1, 5)]
P_HEAD += ["KPI Evidence Verified?", "Manager Comment"]
header(ws_p, 4, P_HEAD, [12, 18] + [8, 11] * 5 + [10] * 9 + [10, 40])
for idx in range(FIRST, LAST + 1):
    c = ws_p.cell(row=idx, column=1, value=f'=IF(Employees!A{idx}="","",Employees!A{idx})')
    style_calc(c)
    c = ws_p.cell(row=idx, column=2, value=f'=IF(Employees!A{idx}="","",Employees!F{idx})')
    style_calc(c)
    p = perf[idx - FIRST] if idx - FIRST < len(perf) else None
    for k in range(5):
        w = p["kpis"][k][0] if p and k < len(p["kpis"]) else None
        a = p["kpis"][k][1] if p and k < len(p["kpis"]) else None
        style_input(ws_p.cell(row=idx, column=3 + 2 * k, value=w), "0%")
        style_input(ws_p.cell(row=idx, column=4 + 2 * k, value=a), "0.0%")
    for k in range(5):
        style_input(ws_p.cell(row=idx, column=13 + k, value=p["comp"][k] if p else None), "0")
    for k in range(4):
        style_input(ws_p.cell(row=idx, column=18 + k, value=p["beh"][k] if p else None), "0")
    style_input(ws_p.cell(row=idx, column=22, value=p["evid"] if p else None))
    style_input(ws_p.cell(row=idx, column=23))
add_num_validation(ws_p, f"M{FIRST}:U{LAST}", 1, 5, whole=True, msg="Ratings must be whole numbers 1–5.")
add_list_validation(ws_p, f"V{FIRST}:V{LAST}", "=L_YesNo")
for k in range(5):
    add_num_validation(ws_p, f"{get_column_letter(3 + 2 * k)}{FIRST}:{get_column_letter(3 + 2 * k)}{LAST}", 0, 1)
    add_num_validation(ws_p, f"{get_column_letter(4 + 2 * k)}{FIRST}:{get_column_letter(4 + 2 * k)}{LAST}", 0, 3)
ws_p.freeze_panes = "C5"

# =====================================================================
# Ranking_Calc
# =====================================================================
ws_r = wb.create_sheet("Ranking_Calc")
title(ws_r, "Scoring, ranking and hybrid bell curve (automatic – do not edit)",
      "Comparison group, rank, curve rating, hybrid rule, calibration override and final rating")
R_HEAD = ["Employee ID", "Seq", "Department", "Job Level", "Grade", "Comparison Group", "KPI Weight Total",
          "KPI 1 Score", "KPI 2 Score", "KPI 3 Score", "KPI 4 Score", "KPI 5 Score", "KPI Score",
          "Competency Score", "Behavior Score", "Final Score", "Score-Based Rating", "Group Size",
          "Rank in Group", "Group Percentile", "Curve Applied?", "Curve Rating", "Proposed (Mode) Rating",
          "System Rating", "Curve Status", "Calibration Row", "FINAL RATING", "Final Rating Label",
          "Company Rank", "Rating Source", "Flags", "ID Count"]
header(ws_r, 4, R_HEAD, [12, 6, 16, 20, 7, 20, 9, 8, 8, 8, 8, 8, 9, 10, 9, 9, 9, 7, 8, 9, 8, 8, 9, 9, 28, 9, 9, 26, 8, 20, 60, 6])
PI = "Performance_Input"
for r_ in range(FIRST, LAST + 1):
    A = f"$A{r_}"
    blank = f'IF({A}="","",'
    f = {}
    f["A"] = f'=IF(Employees!A{r_}="","",Employees!A{r_})'
    f["B"] = f'={blank}ROW()-4)'
    f["C"] = f'={blank}Employees!C{r_})'
    f["D"] = f'={blank}Employees!F{r_})'
    f["E"] = f'={blank}Employees!G{r_})'
    f["F"] = f'={blank}IF(COMP_BASIS="Grade",E{r_},D{r_}))'
    f["G"] = f'={blank}SUM({PI}!C{r_},{PI}!E{r_},{PI}!G{r_},{PI}!I{r_},{PI}!K{r_}))'
    for k, col in enumerate("HIJKL"):
        wcol = get_column_letter(3 + 2 * k)
        acol = get_column_letter(4 + 2 * k)
        f[col] = (f'={blank}IF({PI}!{acol}{r_}="",0,MIN(IF({PI}!$V{r_}="Yes",KPI_MAX,MIN(KPI_MAX,KPI_CAP_NOEVID)),'
                  f'MAX(0,{PI}!{acol}{r_}*100))))')
    f["M"] = (f'={blank}IF(G{r_}=0,0,(N({PI}!C{r_})*H{r_}+N({PI}!E{r_})*I{r_}+N({PI}!G{r_})*J{r_}'
              f'+N({PI}!I{r_})*K{r_}+N({PI}!K{r_})*L{r_})/G{r_}))')
    f["N"] = (f'={blank}IF(COUNT({PI}!M{r_}:Q{r_})=0,0,SUMPRODUCT(COUNTIF({PI}!M{r_}:Q{r_},{{1,2,3,4,5}})*PROF_SCORES)'
              f'/COUNT({PI}!M{r_}:Q{r_})))')
    f["O"] = (f'={blank}IF(COUNT({PI}!R{r_}:U{r_})=0,0,SUMPRODUCT(COUNTIF({PI}!R{r_}:U{r_},{{1,2,3,4,5}})*PROF_SCORES)'
              f'/COUNT({PI}!R{r_}:U{r_})))')
    f["P"] = f'={blank}ROUND(M{r_}*W_KPI+N{r_}*W_COMP+O{r_}*W_BEH,2))'
    f["Q"] = f'={blank}INDEX(BAND_RATING,MATCH(P{r_},BAND_LOWER,1)))'
    f["R"] = f'={blank}COUNTIF($F${FIRST}:$F${LAST},F{r_}))'
    f["S"] = (f'={blank}COUNTIFS($F${FIRST}:$F${LAST},F{r_},$P${FIRST}:$P${LAST},">"&P{r_})'
              f'+COUNTIFS($F${FIRST}:$F${LAST},F{r_},$P${FIRST}:$P${LAST},P{r_},$B${FIRST}:$B${LAST},"<"&B{r_})+1)')
    f["T"] = f'={blank}S{r_}/R{r_})'
    f["U"] = f'={blank}IF(R{r_}>=MIN_GROUP,"Yes","No"))'
    f["V"] = (f'={blank}IF(U{r_}="No",Q{r_},IF(S{r_}<=ROUND(R{r_}*DIST_5,0),5,IF(S{r_}<=ROUND(R{r_}*(DIST_5+DIST_4),0),4,'
              f'IF(S{r_}<=ROUND(R{r_}*(DIST_5+DIST_4+DIST_3),0),3,IF(S{r_}<=ROUND(R{r_}*(DIST_5+DIST_4+DIST_3+DIST_2),0),2,1))))))')
    f["W"] = (f'={blank}IF(CURVE_MODE="Guided",Q{r_},IF(CURVE_MODE="Forced",V{r_},'
              f'Q{r_}+MAX(-MAX_ADJ,MIN(MAX_ADJ,V{r_}-Q{r_})))))')
    f["X"] = (f'={blank}IF(AND(W{r_}<Q{r_},CONFIRM_DOWN="Yes"),Q{r_},IF(AND(W{r_}>Q{r_},CONFIRM_UP="Yes"),Q{r_},W{r_})))')
    f["Y"] = (f'={blank}IF(W{r_}=Q{r_},"No curve change",IF(X{r_}=W{r_},IF(W{r_}>Q{r_},"Curve uplift applied","Curve reduction applied"),'
              f'IF(W{r_}>Q{r_},"Curve uplift pending committee","Curve reduction pending committee"))))')
    f["Z"] = (f'={blank}SUMPRODUCT(MAX((Calibration_Log!$C${LOG_FIRST}:$C${LOG_LAST}={A})'
              f'*Calibration_Log!$P${LOG_FIRST}:$P${LOG_LAST})))')
    f["AA"] = f'={blank}IF(Z{r_}>0,INDEX(Calibration_Log!$E:$E,Z{r_}),X{r_}))'
    f["AB"] = f'={blank}INDEX(BAND_LABEL,AA{r_}))'
    f["AC"] = (f'={blank}COUNTIF($P${FIRST}:$P${LAST},">"&P{r_})+COUNTIFS($P${FIRST}:$P${LAST},P{r_},$B${FIRST}:$B${LAST},"<"&B{r_})+1)')
    f["AD"] = f'={blank}IF(Z{r_}>0,"Calibrated (committee)",IF(X{r_}<>Q{r_},"Curve adjusted","Score bands")))'
    f["AE"] = (f'={blank}TRIM(IF(ROUND(G{r_},4)<>1,"KPI weights not 100%; ","")'
               f'&IF(U{r_}="No","Group below minimum size - curve not applied; ","")'
               f'&IF(ISNUMBER(SEARCH("pending",Y{r_})),"Curve change awaiting committee; ","")'
               f'&IF({PI}!V{r_}<>"Yes","KPI evidence not verified - capped at "&KPI_CAP_NOEVID&"; ","")'
               f'&IF(COUNT({PI}!M{r_}:U{r_})<9,"Missing competency/behavior rating(s); ","")'
               f'&IF(COUNTIFS($F${FIRST}:$F${LAST},F{r_},$P${FIRST}:$P${LAST},P{r_})>1,"Tied score in group; ","")'
               f'&IF(AF{r_}>1,"DUPLICATE ID; ","")))')
    f["AF"] = f'={blank}COUNTIF(Employees!$A${FIRST}:$A${LAST},{A}))'
    for col, formula in f.items():
        c = ws_r[f"{col}{r_}"]
        c.value = formula
        fmt = {"G": "0%", "H": "0.0", "I": "0.0", "J": "0.0", "K": "0.0", "L": "0.0", "M": "0.00", "N": "0.00",
               "O": "0.00", "P": "0.00", "T": "0%"}.get(col)
        style_calc(c, fmt)
    ws_r[f"AA{r_}"].fill = FILL_KEY
    ws_r[f"AA{r_}"].font = F_BOLD
ws_r.freeze_panes = "B5"
ws_r.auto_filter.ref = f"A4:AF{LAST}"
protect(ws_r)

# =====================================================================
# Calibration_Log
# =====================================================================
ws_l = wb.create_sheet("Calibration_Log")
title(ws_l, "Calibration committee – exceptions and decision log",
      "An entry changes the FINAL rating only if Decision = Approved AND Supporting Evidence AND Final Approver are completed. The latest applied entry per employee wins.")
L_HEAD = ["Log ID", "Date", "Employee ID", "Current System Rating", "Proposed Final Rating", "Change Type", "Reason Code",
          "Supporting Evidence", "Manager Justification", "HR Review", "Committee Decision", "Final Approver",
          "Approval Date", "Effective?", "Validation Message", "Applied Row (helper)"]
header(ws_l, 4, L_HEAD, [8, 12, 12, 10, 10, 11, 30, 45, 35, 12, 12, 20, 12, 10, 34, 8])
for r_ in range(LOG_FIRST, LOG_LAST + 1):
    for col in "ABCEGHIJKLM":
        style_input(ws_l[f"{col}{r_}"], {"B": "dd-mmm-yyyy", "M": "dd-mmm-yyyy"}.get(col))
    ws_l[f"A{r_}"].value = f'=IF(C{r_}="","","CAL-"&TEXT(ROW()-4,"000"))'
    style_calc(ws_l[f"A{r_}"])
    calc = {
        "D": f'=IF(C{r_}="","",IFERROR(INDEX(Ranking_Calc!$X${FIRST}:$X${LAST},MATCH(C{r_},Ranking_Calc!$A${FIRST}:$A${LAST},0)),"ID not found"))',
        "F": f'=IF(OR(C{r_}="",E{r_}="",NOT(ISNUMBER(D{r_}))),"",IF(E{r_}>D{r_},"Upgrade",IF(E{r_}<D{r_},"Downgrade","Confirm")))',
        "N": f'=IF(C{r_}="","",IF(AND(K{r_}="Approved",H{r_}<>"",L{r_}<>"",ISNUMBER(D{r_}),ISNUMBER(E{r_})),"Yes","No"))',
        "O": (f'=IF(C{r_}="","",IF(NOT(ISNUMBER(D{r_})),"Unknown employee ID",IF(E{r_}="","Enter proposed rating",'
              f'IF(AND(K{r_}="Approved",H{r_}=""),"Approved without evidence - NOT applied",'
              f'IF(AND(K{r_}="Approved",L{r_}=""),"No final approver - NOT applied",'
              f'IF(N{r_}="Yes","Applied to final rating","Not applied ("&IF(K{r_}="","no decision",K{r_})&")"))))))'),
        "P": f'=IF(N{r_}="Yes",ROW(),0)',
    }
    for col, formula in calc.items():
        ws_l[f"{col}{r_}"].value = formula
        style_calc(ws_l[f"{col}{r_}"])
add_num_validation(ws_l, f"E{LOG_FIRST}:E{LOG_LAST}", 1, 5, whole=True, msg="Rating must be 1–5.")
add_list_validation(ws_l, f"G{LOG_FIRST}:G{LOG_LAST}", "=L_Reason")
add_list_validation(ws_l, f"J{LOG_FIRST}:J{LOG_LAST}", "=L_HRReview")
add_list_validation(ws_l, f"K{LOG_FIRST}:K{LOG_LAST}", "=L_Decision")
ws_l.freeze_panes = "D5"
protect(ws_l)

# =====================================================================
# Bonus
# =====================================================================
ws_b = wb.create_sheet("Bonus")
title(ws_b, "Annual performance bonus (automatic)",
      "Bonus = Annual base × Target % × Company factor × Individual multiplier × Proration × Funding factor")
B_HEAD = ["Employee ID", "Grade", "Final Rating", "Rating Label", "Monthly Basic", "Annual Bonus Base", "Target Bonus %",
          "Target Bonus (SAR)", "Company Factor", "Individual Multiplier", "Eligible Days", "Proration",
          "Bonus Eligible", "Calculated Bonus", "Funding Factor", "FINAL BONUS (SAR)", "Notes"]
header(ws_b, 4, B_HEAD, [12, 7, 8, 26, 11, 13, 9, 12, 9, 10, 9, 9, 9, 13, 9, 14, 40])
for r_ in range(FIRST, LAST + 1):
    blank = f'IF($A{r_}="","",'
    f = {
        "A": f'=IF(Employees!A{r_}="","",Employees!A{r_})',
        "B": f'={blank}Employees!G{r_})',
        "C": f'={blank}Ranking_Calc!AA{r_})',
        "D": f'={blank}Ranking_Calc!AB{r_})',
        "E": f'={blank}Employees!K{r_})',
        "F": f'={blank}E{r_}*BONUS_MONTHS)',
        "G": f'={blank}IFERROR(INDEX(GRADE_TGT,MATCH(B{r_},GRADE_LIST,0)),0))',
        "H": f'={blank}F{r_}*G{r_})',
        "I": f'={blank}CPF)',
        "J": f'={blank}INDEX(BONUS_MULT,C{r_}))',
        "K": (f'={blank}MAX(0,IF(Employees!I{r_}="",CYCLE_END,MIN(Employees!I{r_},CYCLE_END))'
              f'-MAX(Employees!H{r_},CYCLE_START)+1-N(Employees!J{r_})))'),
        "L": f'={blank}IF(K{r_}<MIN_SERVICE,0,K{r_}/(CYCLE_END-CYCLE_START+1)))',
        "M": f'={blank}Employees!L{r_})',
        "N": f'={blank}IF(M{r_}="Yes",ROUND(H{r_}*I{r_}*J{r_}*L{r_},2),0))',
        "O": f'={blank}FUNDING_FACTOR)',
        "P": f'={blank}ROUND(N{r_}*O{r_},2))',
        "Q": (f'={blank}IF(M{r_}<>"Yes","Not bonus eligible (contract)",IF(L{r_}=0,"Below minimum service",'
              f'IF(Employees!I{r_}<>"","Leaver - validate payment rule with Legal",IF(L{r_}<1,"Prorated","")))))'),
    }
    for col, formula in f.items():
        c = ws_b[f"{col}{r_}"]
        c.value = formula
        style_calc(c, {"E": "#,##0", "F": "#,##0", "G": "0%", "H": "#,##0", "I": "0.0000", "J": "0.00",
                       "K": "0", "L": "0.0000", "N": "#,##0.00", "O": "0.0000", "P": "#,##0.00"}.get(col))
    ws_b[f"P{r_}"].fill = FILL_KEY
    ws_b[f"P{r_}"].font = F_BOLD
ws_b.freeze_panes = "B5"
ws_b.auto_filter.ref = f"A4:Q{LAST}"
protect(ws_b)

# =====================================================================
# Merit
# =====================================================================
ws_mr = wb.create_sheet("Merit")
title(ws_mr, "Annual merit salary increase (automatic)",
      "Merit % = Matrix(final rating, compa-ratio band) × budget scale, capped · increases above range max flagged, not truncated")
M_HEAD = ["Employee ID", "Grade", "Final Rating", "Monthly Basic", "Range Min", "Range Mid", "Range Max", "Compa-Ratio %",
          "CR Band", "Matrix %", "Merit Eligible", "Budget Scale", "MERIT %", "Monthly Increase", "New Monthly Basic",
          "New Compa-Ratio %", "Annual Cost (SAR)", "Status", "Unscaled Annual Cost"]
header(ws_mr, 4, M_HEAD, [12, 7, 8, 11, 10, 10, 10, 10, 12, 9, 9, 9, 9, 11, 12, 10, 12, 36, 12])
for r_ in range(FIRST, LAST + 1):
    blank = f'IF($A{r_}="","",'
    f = {
        "A": f'=IF(Employees!A{r_}="","",Employees!A{r_})',
        "B": f'={blank}Employees!G{r_})',
        "C": f'={blank}Ranking_Calc!AA{r_})',
        "D": f'={blank}Employees!K{r_})',
        "E": f'={blank}INDEX(GRADE_MIN,MATCH(B{r_},GRADE_LIST,0)))',
        "F": f'={blank}INDEX(GRADE_MID,MATCH(B{r_},GRADE_LIST,0)))',
        "G": f'={blank}INDEX(GRADE_MAX,MATCH(B{r_},GRADE_LIST,0)))',
        "H": f'={blank}ROUND(D{r_}/F{r_}*100,2))',
        "I": f'={blank}INDEX(CR_LABELS,MATCH(H{r_},CR_LOWER,1)))',
        "J": f'={blank}INDEX(MERIT_MATRIX,6-C{r_},MATCH(H{r_},CR_LOWER,1)))',
        "K": (f'={blank}IF(AND(Employees!M{r_}="Yes",Employees!H{r_}<MERIT_CUTOFF,Employees!I{r_}=""),"Yes","No"))'),
        "L": f'={blank}MERIT_SCALE)',
        "M": f'={blank}IF(K{r_}="Yes",MIN(MERIT_MAX,J{r_}*L{r_}),0))',
        "N": f'={blank}ROUND(D{r_}*M{r_},2))',
        "O": f'={blank}D{r_}+N{r_})',
        "P": f'={blank}ROUND(O{r_}/F{r_}*100,2))',
        "Q": f'={blank}N{r_}*12)',
        "R": (f'={blank}IF(K{r_}<>"Yes","Not eligible",IF(D{r_}>=G{r_},"REVIEW - salary at/above range max",'
              f'IF(O{r_}>G{r_},"REVIEW - new salary exceeds range max",IF(D{r_}<E{r_},"Below range min - consider equity review",'
              f'IF(M{r_}>0,"Proposed","No increase (rating/position)"))))))'),
        "S": f'={blank}IF(K{r_}="Yes",D{r_}*J{r_}*12,0))',
    }
    for col, formula in f.items():
        c = ws_mr[f"{col}{r_}"]
        c.value = formula
        style_calc(c, {"D": "#,##0", "E": "#,##0", "F": "#,##0", "G": "#,##0", "H": "0.00", "J": "0.0%",
                       "L": "0.0000", "M": "0.00%", "N": "#,##0.00", "O": "#,##0.00", "P": "0.00",
                       "Q": "#,##0.00", "S": "#,##0.00"}.get(col))
    ws_mr[f"M{r_}"].fill = FILL_KEY
    ws_mr[f"M{r_}"].font = F_BOLD
ws_mr.freeze_panes = "B5"
ws_mr.auto_filter.ref = f"A4:S{LAST}"
protect(ws_mr)

# =====================================================================
# Budget_Control
# =====================================================================
ws_bc = wb.create_sheet("Budget_Control")
title(ws_bc, "Budget controls – bonus and merit", "Ratings are never changed to meet a budget.")
ws_bc.column_dimensions["A"].width = 52
ws_bc.column_dimensions["B"].width = 18
ws_bc.column_dimensions["C"].width = 18
ws_bc.column_dimensions["D"].width = 18
ws_bc.column_dimensions["E"].width = 18
ws_bc.column_dimensions["F"].width = 60
BRows = [
    ("BONUS", None, None, None),
    ("Bonus budget (SAR)", "=BONUS_BUDGET", "#,##0", "BC_BONUS_BUDGET"),
    ("Target bonus pool – eligible employees (SAR)", f'=SUMIF(Bonus!M{FIRST}:M{LAST},"Yes",Bonus!H{FIRST}:H{LAST})', "#,##0", "BC_TARGET_POOL"),
    ("Calculated bonus liability before funding factor (SAR)", f"=SUM(Bonus!N{FIRST}:N{LAST})", "#,##0", "BC_LIABILITY"),
    ("Funding factor applied", '=IF(AND(APPLY_FF="Yes",BC_LIABILITY>BC_BONUS_BUDGET,BC_LIABILITY>0),BC_BONUS_BUDGET/BC_LIABILITY,1)', "0.0000", "FUNDING_FACTOR"),
    ("Final bonus payout (SAR)", f"=SUM(Bonus!P{FIRST}:P{LAST})", "#,##0", "BC_BONUS_FINAL"),
    ("Remaining budget (SAR)", "=BC_BONUS_BUDGET-BC_BONUS_FINAL", "#,##0", "BC_BONUS_REMAIN"),
    ("Budget utilisation", "=IF(BC_BONUS_BUDGET=0,0,BC_BONUS_FINAL/BC_BONUS_BUDGET)", "0.0%", "BC_BONUS_UTIL"),
    ("Payout as % of target pool", "=IF(BC_TARGET_POOL=0,0,BC_BONUS_FINAL/BC_TARGET_POOL)", "0.0%", None),
    ("Bonus budget status", '=IF(BC_BONUS_FINAL<=BC_BONUS_BUDGET+0.5,"Within budget","OVER BUDGET - set Apply funding factor or seek approval")', None, "BC_BONUS_STATUS"),
    ("", None, None, None),
    ("MERIT", None, None, None),
    ("Eligible annual base payroll (SAR)", f'=SUMIF(Merit!K{FIRST}:K{LAST},"Yes",Merit!D{FIRST}:D{LAST})*12', "#,##0", "BC_PAYROLL"),
    ("Merit budget %", "=MERIT_BUDGET_PCT", "0.0%", None),
    ("Merit budget (SAR, annual)", "=BC_PAYROLL*MERIT_BUDGET_PCT", "#,##0", "BC_MERIT_BUDGET"),
    ("Matrix cost before scaling (SAR, annual)", f"=SUM(Merit!S{FIRST}:S{LAST})", "#,##0", "BC_MERIT_UNSCALED"),
    ("Scale factor that would fit the budget", "=IF(BC_MERIT_UNSCALED=0,0,BC_MERIT_BUDGET/BC_MERIT_UNSCALED)", "0.0000", "BC_MERIT_FIT"),
    ("Budget scale applied", '=IF(SCALE_TO_BUDGET="Yes",BC_MERIT_FIT,1)', "0.0000", "MERIT_SCALE"),
    ("Final merit cost (SAR, annual)", f"=SUM(Merit!Q{FIRST}:Q{LAST})", "#,##0", "BC_MERIT_FINAL"),
    ("Final merit cost as % of eligible payroll", "=IF(BC_PAYROLL=0,0,BC_MERIT_FINAL/BC_PAYROLL)", "0.00%", None),
    ("Variance vs budget (SAR; + = under budget)", "=BC_MERIT_BUDGET-BC_MERIT_FINAL", "#,##0", "BC_MERIT_VAR"),
    ("Employees receiving an increase", f'=COUNTIF(Merit!M{FIRST}:M{LAST},">0")', "0", None),
    ("Eligible employees with no increase", f'=COUNTIFS(Merit!K{FIRST}:K{LAST},"Yes",Merit!M{FIRST}:M{LAST},0)', "0", None),
    ("Cases flagged for range-max review", f'=COUNTIF(Merit!R{FIRST}:R{LAST},"REVIEW*")', "0", None),
    ("Merit budget status", '=IF(BC_MERIT_FINAL<=BC_MERIT_BUDGET+0.5,"Within budget","OVER BUDGET")', None, "BC_MERIT_STATUS"),
]
r_ = 4
for lab, formula, fmt, nm in BRows:
    if formula is None:
        ws_bc.cell(row=r_, column=1, value=lab).font = F_SECTION
    else:
        ws_bc.cell(row=r_, column=1, value=lab).border = BORDER
        c = ws_bc.cell(row=r_, column=2, value=formula)
        style_calc(c, fmt)
        c.font = F_BOLD
        if nm:
            define(nm, f"Budget_Control!$B${r_}")
    r_ += 1
r_ += 1
ws_bc.cell(row=r_, column=1, value="MERIT BUDGET SIMULATION (matrix shape unchanged)").font = F_SECTION
r_ += 1
for i, h in enumerate(["Scenario", "Budget %", "Budget (SAR)", "Matrix cost unscaled (SAR)", "Scale needed"], start=1):
    c = ws_bc.cell(row=r_, column=i, value=h)
    c.font, c.fill, c.alignment = F_HEAD, FILL_HEAD, CENTER
r_ += 1
for lab, b in (("2% budget", "0.02"), ("3% budget", "0.03"), ("4% budget", "0.04"), ("Custom", "MERIT_CUSTOM")):
    ws_bc.cell(row=r_, column=1, value=lab).border = BORDER
    style_calc(ws_bc.cell(row=r_, column=2, value=f"={b}"), "0.0%")
    style_calc(ws_bc.cell(row=r_, column=3, value=f"=BC_PAYROLL*B{r_}"), "#,##0")
    style_calc(ws_bc.cell(row=r_, column=4, value="=BC_MERIT_UNSCALED"), "#,##0")
    style_calc(ws_bc.cell(row=r_, column=5, value=f"=IF(D{r_}=0,0,C{r_}/D{r_})"), "0.00")
    r_ += 1
ws_bc.cell(row=r_ + 1, column=1, value="Note: scaling multiplies every matrix cell by the same factor; individual increases remain capped at the maximum merit %, so the final cost can be slightly below budget.").alignment = WRAP
protect(ws_bc)

# =====================================================================
# Group_Analysis
# =====================================================================
ws_g = wb.create_sheet("Group_Analysis")
title(ws_g, "Distribution by comparison group (final ratings vs guideline)",
      "Flag = group large enough for the curve AND a rating share differs from guideline by more than the tolerance")
G_HEAD = ["Group", "Headcount", "Curve Applied?", "# 5", "# 4", "# 3", "# 2", "# 1", "% 5", "% 4", "% 3", "% 2", "% 1",
          "Max variance (pp)", "Flag", "Avg Final Score"]
gr = 4


def group_block(label, groups, keycol):
    global gr
    ws_g.cell(row=gr, column=1, value=label).font = F_SECTION
    gr += 1
    header(ws_g, gr, G_HEAD, [24, 10, 10, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 10, 22, 10])
    gr += 1
    first = gr
    for g in groups:
        ws_g.cell(row=gr, column=1, value=g).border = BORDER
        rg = f"Ranking_Calc!${keycol}${FIRST}:${keycol}${LAST}"
        rat = f"Ranking_Calc!$AA${FIRST}:$AA${LAST}"
        style_calc(ws_g.cell(row=gr, column=2, value=f'=COUNTIF({rg},A{gr})'), "0")
        style_calc(ws_g.cell(row=gr, column=3, value=f'=IF(B{gr}>=MIN_GROUP,"Yes","No - too small")'))
        for j, rt in enumerate((5, 4, 3, 2, 1)):
            cl = get_column_letter(4 + j)
            style_calc(ws_g.cell(row=gr, column=4 + j, value=f'=COUNTIFS({rg},A{gr},{rat},{rt})'), "0")
            style_calc(ws_g.cell(row=gr, column=9 + j, value=f'=IF($B{gr}=0,0,{cl}{gr}/$B{gr})'), "0%")
        style_calc(ws_g.cell(row=gr, column=14, value=(
            f'=IF(B{gr}=0,0,MAX(ABS(I{gr}-DIST_5),ABS(J{gr}-DIST_4),ABS(K{gr}-DIST_3),ABS(L{gr}-DIST_2),ABS(M{gr}-DIST_1)))')), "0.0%")
        style_calc(ws_g.cell(row=gr, column=15, value=(
            f'=IF(B{gr}=0,"",IF(B{gr}<MIN_GROUP,"Small group - qualitative review",IF(N{gr}>DIST_TOL,"REVIEW - outside tolerance","Within tolerance")))')))
        style_calc(ws_g.cell(row=gr, column=16, value=(
            f'=IFERROR(AVERAGEIF({rg},A{gr},Ranking_Calc!$P${FIRST}:$P${LAST}),"")')), "0.00")
        gr += 1
    ws_g.cell(row=gr, column=1, value="Guideline").font = F_BOLD
    for j, rt in enumerate((5, 4, 3, 2, 1)):
        style_calc(ws_g.cell(row=gr, column=9 + j, value=f"=DIST_{rt}"), "0%")
    gr += 3
    return first


group_block("By Job Level", LISTS["JobLevel"], "D")
group_block("By Grade", [g[0] for g in GRADES], "E")
group_block("By Department (information only – departments are not comparison groups)", LISTS["Department"], "C")
protect(ws_g)

# =====================================================================
# Checks
# =====================================================================
ws_k = wb.create_sheet("Checks")
title(ws_k, "Model integrity checks", "All checks must PASS before results are released")
header(ws_k, 4, ["#", "Check", "Result", "Status", "What to do if FAIL"], [5, 60, 16, 10, 60])
EMP = f"Employees!$A${FIRST}:$A${LAST}"
CHECKS = [
    ("Performance weights total 100%", "=W_TOTAL", "=IF(ABS(C{r}-1)<0.0001,\"PASS\",\"FAIL\")", "Fix Config section B", "0%"),
    ("Guideline distribution totals 100%", "=DIST_TOTAL", "=IF(ABS(C{r}-1)<0.0001,\"PASS\",\"FAIL\")", "Fix Config section F", "0.0%"),
    ("Rating band lower bounds ascending", "=IF(AND(INDEX(BAND_LOWER,1)<INDEX(BAND_LOWER,2),INDEX(BAND_LOWER,2)<INDEX(BAND_LOWER,3),INDEX(BAND_LOWER,3)<INDEX(BAND_LOWER,4),INDEX(BAND_LOWER,4)<INDEX(BAND_LOWER,5)),\"OK\",\"Not ascending\")", "=IF(C{r}=\"OK\",\"PASS\",\"FAIL\")", "Fix Config section E", None),
    ("Company scorecard weights total 100%", "=SUM(CS_WEIGHTS)", "=IF(ABS(C{r}-1)<0.0001,\"PASS\",\"FAIL\")", "Fix Config section G", "0%"),
    ("Employees loaded", f"=COUNTA({EMP})", "=IF(C{r}>0,\"PASS\",\"FAIL\")", "Enter employees", "0"),
    ("Duplicate Employee IDs", f"=COUNTIF(Ranking_Calc!$AF${FIRST}:$AF${LAST},\">1\")", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Remove duplicate IDs in Employees", "0"),
    ("Grades not found in salary range table", f"=SUMPRODUCT((Employees!$G${FIRST}:$G${LAST}<>\"\")*(COUNTIF(GRADE_LIST,Employees!$G${FIRST}:$G${LAST})=0))", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Add the grade to Config section I", "0"),
    ("Missing salary or hire date", f"=SUMPRODUCT((Employees!$A${FIRST}:$A${LAST}<>\"\")*((Employees!$K${FIRST}:$K${LAST}=\"\")+(Employees!$H${FIRST}:$H${LAST}=\"\")>0))", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Complete Employees columns H and K", "0"),
    ("Employees whose KPI weights do not total 100%", f"=COUNTIF(Ranking_Calc!$AE${FIRST}:$AE${LAST},\"*KPI weights not 100%*\")", "=IF(C{r}=0,\"PASS\",\"WARN\")", "Correct weights in Performance_Input", "0"),
    ("Employees with missing competency/behavior ratings", f"=COUNTIF(Ranking_Calc!$AE${FIRST}:$AE${LAST},\"*Missing competency*\")", "=IF(C{r}=0,\"PASS\",\"WARN\")", "Complete ratings or document reason", "0"),
    ("Final ratings outside 1–5", f"=COUNTIF(Ranking_Calc!$AA${FIRST}:$AA${LAST},\"<1\")+COUNTIF(Ranking_Calc!$AA${FIRST}:$AA${LAST},\">5\")+SUMPRODUCT((Ranking_Calc!$A${FIRST}:$A${LAST}<>\"\")*NOT(ISNUMBER(Ranking_Calc!$AA${FIRST}:$AA${LAST})))", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Check Calibration_Log ratings", "0"),
    ("Curve changes awaiting committee", f"=COUNTIF(Ranking_Calc!$Y${FIRST}:$Y${LAST},\"*pending*\")", "=IF(C{r}=0,\"PASS\",\"WARN\")", "Committee to confirm or reject in Calibration_Log", "0"),
    ("Calibration entries Approved but not applied (missing evidence/approver/ID)", f"=COUNTIFS(Calibration_Log!$K${LOG_FIRST}:$K${LOG_LAST},\"Approved\",Calibration_Log!$N${LOG_FIRST}:$N${LOG_LAST},\"No\")", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Complete evidence and final approver", "0"),
    ("Bonus total reconciles with Dashboard", "=ABS(ROUND(BC_BONUS_FINAL-Dashboard!$D$26,0))+ABS(ROUND(BC_BONUS_FINAL-Dashboard!$E$38,0))", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Formula error – investigate", "#,##0"),
    ("Bonus payout within budget", "=BC_BONUS_STATUS", "=IF(C{r}=\"Within budget\",\"PASS\",\"WARN\")", "Apply funding factor or obtain approval", None),
    ("Merit cost within budget", "=BC_MERIT_STATUS", "=IF(C{r}=\"Within budget\",\"PASS\",\"WARN\")", "Scale matrix or obtain approval", None),
    ("Merit cases needing range-max review", f"=COUNTIF(Merit!$R${FIRST}:$R${LAST},\"REVIEW*\")", "=IF(C{r}=0,\"PASS\",\"WARN\")", "HR/Finance decide: approve, cap or lump sum", "0"),
    ("Formula errors in calculation sheets", f"=SUMPRODUCT(--ISERROR(Ranking_Calc!$A${FIRST}:$AF${LAST}))+SUMPRODUCT(--ISERROR(Bonus!$A${FIRST}:$Q${LAST}))+SUMPRODUCT(--ISERROR(Merit!$A${FIRST}:$S${LAST}))", "=IF(C{r}=0,\"PASS\",\"FAIL\")", "Check inputs for invalid values", "0"),
]
for i, (lab, res, st, todo, fmt) in enumerate(CHECKS, start=1):
    r = 4 + i
    ws_k.cell(row=r, column=1, value=i).border = BORDER
    ws_k.cell(row=r, column=2, value=lab).border = BORDER
    style_calc(ws_k.cell(row=r, column=3, value=res), fmt)
    style_calc(ws_k.cell(row=r, column=4, value=st.format(r=r)))
    ws_k.cell(row=r, column=5, value=todo).border = BORDER
last_check = 4 + len(CHECKS)
ws_k.cell(row=last_check + 2, column=2, value="OVERALL STATUS").font = F_BOLD
c = ws_k.cell(row=last_check + 2, column=4,
              value=f'=IF(COUNTIF(D5:D{last_check},"FAIL")>0,"FAIL",IF(COUNTIF(D5:D{last_check},"WARN")>0,"REVIEW","ALL PASS"))')
c.font = F_BOLD
define("CHECK_STATUS", f"Checks!$D${last_check + 2}")
define("CHECK_FAILS", f"Checks!$D$5:$D${last_check}")
red = PatternFill("solid", fgColor="F8CBAD")
green = PatternFill("solid", fgColor="C6EFCE")
amber = PatternFill("solid", fgColor="FFEB9C")
ws_k.conditional_formatting.add(f"D5:D{last_check + 2}", CellIsRule(operator="equal", formula=['"FAIL"'], fill=red))
ws_k.conditional_formatting.add(f"D5:D{last_check + 2}", CellIsRule(operator="equal", formula=['"PASS"'], fill=green))
ws_k.conditional_formatting.add(f"D5:D{last_check + 2}", CellIsRule(operator="equal", formula=['"ALL PASS"'], fill=green))
ws_k.conditional_formatting.add(f"D5:D{last_check + 2}", CellIsRule(operator="equal", formula=['"WARN"'], fill=amber))
ws_k.conditional_formatting.add(f"D5:D{last_check + 2}", CellIsRule(operator="equal", formula=['"REVIEW"'], fill=amber))
protect(ws_k)

# =====================================================================
# Audit_Trail
# =====================================================================
ws_a = wb.create_sheet("Audit_Trail")
title(ws_a, "Audit trail – record every change, approval and release",
      "Excel cannot log changes automatically without macros (macro-free by design for security). Each change must be recorded here by the person making it.")
A_HEAD = ["Entry #", "Date", "Changed By", "Role", "Sheet", "Item / Cell", "Old Value", "New Value", "Reason",
          "Approved By", "Model Version", "Bonus Total at Save", "Merit Cost at Save", "Check Status at Save"]
header(ws_a, 4, A_HEAD, [7, 12, 16, 14, 16, 22, 14, 14, 40, 16, 9, 14, 14, 12])
SAMPLE_AUDIT = [
    (date(2026, 11, 8), "HR Rewards", "HR Administrator", "All", "Model build", "", "v1.0", "Model created with synthetic sample data", "HR Director", "1.0"),
    (date(2026, 11, 8), "HR Rewards", "HR Administrator", "Config", "Rating bands (C)", "", "Option A", "Phase 1 recommendation; decision D-07 pending executive approval", "Pending", "1.0"),
]
for i in range(AUD_FIRST, AUD_LAST + 1):
    for col in range(1, 15):
        style_input(ws_a.cell(row=i, column=col), "dd-mmm-yyyy" if col == 2 else ("#,##0" if col in (12, 13) else None))
    ws_a.cell(row=i, column=1, value=f'=IF(B{i}="","",ROW()-4)')
    style_calc(ws_a.cell(row=i, column=1))
for j, entry in enumerate(SAMPLE_AUDIT):
    for col, v in enumerate(entry, start=2):
        ws_a.cell(row=AUD_FIRST + j, column=col, value=v)
ws_a.cell(row=2, column=8, value="Current control totals (copy as values into your entry):").font = F_BOLD
ws_a["L2"] = "=BC_BONUS_FINAL"
ws_a["M2"] = "=BC_MERIT_FINAL"
ws_a["N2"] = "=CHECK_STATUS"
for cc in ("L2", "M2"):
    ws_a[cc].number_format = "#,##0"
    ws_a[cc].fill = FILL_KEY
ws_a["N2"].fill = FILL_KEY
ws_a.freeze_panes = "B5"

# =====================================================================
# Dashboard (built last so it can reference everything)
# =====================================================================
ws_d = wb.create_sheet("Dashboard", 1)
title(ws_d, "Enerco – Performance, Bell Curve & Rewards Dashboard", "")
ws_d["A2"] = '="Cycle "&CYCLE_YEAR&"  ·  Curve mode: "&CURVE_MODE&"  ·  Comparison basis: "&COMP_BASIS&"  ·  Company factor: "&TEXT(CPF,"0.00")&"  ·  Model checks: "&CHECK_STATUS'
ws_d["A2"].font = Font(size=11, bold=True, color=TEAL)
for col, w in zip("ABCDEFGHIJKLMN", (16, 26, 14, 22, 14, 14, 14, 14, 3, 14, 16, 14, 14, 14)):
    ws_d.column_dimensions[col].width = w

RC = "Ranking_Calc"
tiles = [("Employees", f'=COUNTA(Employees!$A${FIRST}:$A${LAST})', "0"),
         ("Average final score", f'=IFERROR(AVERAGE({RC}!$P${FIRST}:$P${LAST}),0)', "0.00"),
         ("Final bonus payout (SAR)", "=BC_BONUS_FINAL", "#,##0"),
         ("Bonus budget used", "=BC_BONUS_UTIL", "0.0%"),
         ("Merit cost, annual (SAR)", "=BC_MERIT_FINAL", "#,##0"),
         ("Merit cost % of payroll", "=IF(BC_PAYROLL=0,0,BC_MERIT_FINAL/BC_PAYROLL)", "0.00%"),
         ("Merit budget (SAR)", "=BC_MERIT_BUDGET", "#,##0")]
for i, (lab, formula, fmt) in enumerate(tiles):
    col = 1 + i * 2 if i < 4 else 1 + (i - 4) * 2
    rr = 4 if i < 4 else 7
    c1 = ws_d.cell(row=rr, column=col, value=lab)
    c1.font = Font(size=9, bold=True, color="595959")
    c2 = ws_d.cell(row=rr + 1, column=col, value=formula)
    c2.font = Font(size=16, bold=True, color=NAVY)
    c2.number_format = fmt
    c2.fill = FILL_KEY

# Distribution table (rows 11-17)
ws_d["A10"] = "1. Rating distribution – company"
ws_d["A10"].font = F_SECTION
header(ws_d, 11, ["Rating", "Label", "Guideline %", "Guideline #", "Score-based #", "FINAL #", "FINAL %", "Variance (pp)"])
for col, w in zip("ABCDEFGH", (16, 26, 14, 22, 14, 14, 14, 14)):
    ws_d.column_dimensions[col].width = w
for i, rt in enumerate((5, 4, 3, 2, 1)):
    rr = 12 + i
    vals = [rt, f"=INDEX(BAND_LABEL,{rt})", f"=DIST_{rt}", f"=ROUND(COUNTA(Employees!$A${FIRST}:$A${LAST})*DIST_{rt},1)",
            f"=COUNTIF({RC}!$Q${FIRST}:$Q${LAST},{rt})", f"=COUNTIF({RC}!$AA${FIRST}:$AA${LAST},{rt})",
            f"=IF(SUM($F$12:$F$16)=0,0,F{rr}/SUM($F$12:$F$16))", f"=(G{rr}-C{rr})*100"]
    for j, v in enumerate(vals, start=1):
        c = ws_d.cell(row=rr, column=j, value=v)
        style_calc(c, {3: "0%", 4: "0.0", 7: "0.0%", 8: "+0.0;-0.0;0.0"}.get(j))
ws_d["A17"] = "Total"
ws_d["A17"].font = F_BOLD
for j, col in enumerate("CDEFG", start=3):
    style_calc(ws_d.cell(row=17, column=j, value=f"=SUM({col}12:{col}16)"), {3: "0%", 4: "0.0", 7: "0.0%"}.get(j))

# Rewards by rating (rows 20-26)
ws_d["A19"] = "2. Rewards by final rating"
ws_d["A19"].font = F_SECTION
header(ws_d, 20, ["Rating", "Label", "Employees", "Bonus (SAR)", "Avg bonus (SAR)", "Merit cost (SAR/yr)", "Avg merit %", "Multiplier"])
for i, rt in enumerate((5, 4, 3, 2, 1)):
    rr = 21 + i
    vals = [rt, f"=INDEX(BAND_LABEL,{rt})", f"=COUNTIF(Bonus!$C${FIRST}:$C${LAST},{rt})",
            f"=SUMIF(Bonus!$C${FIRST}:$C${LAST},{rt},Bonus!$P${FIRST}:$P${LAST})",
            f"=IF(C{rr}=0,0,D{rr}/C{rr})", f"=SUMIF(Merit!$C${FIRST}:$C${LAST},{rt},Merit!$Q${FIRST}:$Q${LAST})",
            f'=IFERROR(AVERAGEIFS(Merit!$M${FIRST}:$M${LAST},Merit!$C${FIRST}:$C${LAST},{rt},Merit!$K${FIRST}:$K${LAST},"Yes"),0)',
            f"=INDEX(BONUS_MULT,{rt})"]
    for j, v in enumerate(vals, start=1):
        style_calc(ws_d.cell(row=rr, column=j, value=v), {4: "#,##0", 5: "#,##0", 6: "#,##0", 7: "0.00%", 8: "0.00"}.get(j))
ws_d["A26"] = "Total"
ws_d["A26"].font = F_BOLD
for j, col in ((3, "C"), (4, "D"), (6, "F")):
    style_calc(ws_d.cell(row=26, column=j, value=f"=SUM({col}21:{col}25)"), "#,##0")

# Department table (rows 29-38)
ws_d["A28"] = "3. Costs by department"
ws_d["A28"].font = F_SECTION
header(ws_d, 29, ["Department", "", "Headcount", "Avg score", "Bonus (SAR)", "Merit cost (SAR/yr)", "# Rated 4–5", "# Rated 1–2"])
for i, d in enumerate(LISTS["Department"]):
    rr = 30 + i
    vals = [d, "", f"=COUNTIF({RC}!$C${FIRST}:$C${LAST},A{rr})",
            f'=IFERROR(AVERAGEIF({RC}!$C${FIRST}:$C${LAST},A{rr},{RC}!$P${FIRST}:$P${LAST}),0)',
            f"=SUMIF(Employees!$C${FIRST}:$C${LAST},A{rr},Bonus!$P${FIRST}:$P${LAST})",
            f"=SUMIF(Employees!$C${FIRST}:$C${LAST},A{rr},Merit!$Q${FIRST}:$Q${LAST})",
            f'=COUNTIFS({RC}!$C${FIRST}:$C${LAST},A{rr},{RC}!$AA${FIRST}:$AA${LAST},">=4")',
            f'=COUNTIFS({RC}!$C${FIRST}:$C${LAST},A{rr},{RC}!$AA${FIRST}:$AA${LAST},"<=2")']
    for j, v in enumerate(vals, start=1):
        style_calc(ws_d.cell(row=rr, column=j, value=v), {4: "0.00", 5: "#,##0", 6: "#,##0"}.get(j))
ws_d["A38"] = "Total"
ws_d["A38"].font = F_BOLD
for j, col in ((3, "C"), (5, "E"), (6, "F")):
    style_calc(ws_d.cell(row=38, column=j, value=f"=SUM({col}30:{col}37)"), "#,##0")

# Top 20 ranking (rows 43-63)
ws_d["A42"] = "4. Company ranking – top 20 by final score"
ws_d["A42"].font = F_SECTION
header(ws_d, 43, ["Company rank", "Employee ID", "Department", "Job Level", "Final score", "Rank in group", "Final rating", "Bonus (SAR)"])
for k in range(1, 21):
    rr = 43 + k
    m = f"MATCH({k},{RC}!$AC${FIRST}:$AC${LAST},0)"
    vals = [k, f"=IFERROR(INDEX({RC}!$A${FIRST}:$A${LAST},{m}),\"\")", f"=IFERROR(INDEX({RC}!$C${FIRST}:$C${LAST},{m}),\"\")",
            f"=IFERROR(INDEX({RC}!$D${FIRST}:$D${LAST},{m}),\"\")", f"=IFERROR(INDEX({RC}!$P${FIRST}:$P${LAST},{m}),\"\")",
            f'=IFERROR(INDEX({RC}!$S${FIRST}:$S${LAST},{m})&" of "&INDEX({RC}!$R${FIRST}:$R${LAST},{m}),"")',
            f"=IFERROR(INDEX({RC}!$AA${FIRST}:$AA${LAST},{m}),\"\")", f"=IFERROR(INDEX(Bonus!$P${FIRST}:$P${LAST},{m}),\"\")"]
    for j, v in enumerate(vals, start=1):
        c = ws_d.cell(row=rr, column=j, value=v)
        style_calc(c, {5: "0.00", 8: "#,##0"}.get(j))
        if j in (1, 6, 7):
            c.alignment = Alignment(horizontal="center")

# Group summary (rows 66+)
ws_d["A66"] = "5. Comparison groups (Job Level) – final distribution"
ws_d["A66"].font = F_SECTION
header(ws_d, 67, ["Job Level", "", "Headcount", "% rated 5", "% rated 4", "% rated 3", "% rated 2", "% rated 1"])
for i, lvl in enumerate(LISTS["JobLevel"]):
    rr = 68 + i
    ws_d.cell(row=rr, column=1, value=lvl).border = BORDER
    style_calc(ws_d.cell(row=rr, column=3, value=f"=COUNTIF({RC}!$D${FIRST}:$D${LAST},A{rr})"), "0")
    for j, rt in enumerate((5, 4, 3, 2, 1)):
        style_calc(ws_d.cell(row=rr, column=4 + j, value=(
            f"=IF(C{rr}=0,0,COUNTIFS({RC}!$D${FIRST}:$D${LAST},A{rr},{RC}!$AA${FIRST}:$AA${LAST},{rt})/C{rr})")), "0%")
ws_d.cell(row=72, column=1, value="Guideline").font = F_BOLD
for j, rt in enumerate((5, 4, 3, 2, 1)):
    style_calc(ws_d.cell(row=72, column=4 + j, value=f"=DIST_{rt}"), "0%")

# Charts
ch = BarChart()
ch.type = "col"
ch.title = "Final rating distribution vs guideline"
ch.y_axis.title = "% of employees"
ch.y_axis.numFmt = "0%"
data = Reference(ws_d, min_col=3, min_row=11, max_row=16)
ch.add_data(data, titles_from_data=True)
data2 = Reference(ws_d, min_col=7, min_row=11, max_row=16)
ch.add_data(data2, titles_from_data=True)
ch.set_categories(Reference(ws_d, min_col=2, min_row=12, max_row=16))
ch.height, ch.width = 8, 16
ws_d.add_chart(ch, "J4")

ch2 = BarChart()
ch2.type = "col"
ch2.title = "Bonus and merit cost by final rating (SAR)"
ch2.add_data(Reference(ws_d, min_col=4, min_row=20, max_row=25), titles_from_data=True)
ch2.add_data(Reference(ws_d, min_col=6, min_row=20, max_row=25), titles_from_data=True)
ch2.set_categories(Reference(ws_d, min_col=2, min_row=21, max_row=25))
ch2.height, ch2.width = 8, 16
ws_d.add_chart(ch2, "J21")

ch3 = BarChart()
ch3.type = "bar"
ch3.title = "Bonus by department (SAR)"
ch3.add_data(Reference(ws_d, min_col=5, min_row=29, max_row=37), titles_from_data=True)
ch3.set_categories(Reference(ws_d, min_col=1, min_row=30, max_row=37))
ch3.legend = None
ch3.height, ch3.width = 8, 16
ws_d.add_chart(ch3, "J38")
protect(ws_d)

# Conditional formatting on ratings
for ws_, rng_ in ((ws_r, f"AA{FIRST}:AA{LAST}"), (ws_b, f"C{FIRST}:C{LAST}"), (ws_mr, f"C{FIRST}:C{LAST}"),
                  (ws_d, "G44:G63")):
    ws_.conditional_formatting.add(rng_, CellIsRule(operator="equal", formula=["5"], fill=PatternFill("solid", fgColor="63BE7B")))
    ws_.conditional_formatting.add(rng_, CellIsRule(operator="equal", formula=["4"], fill=PatternFill("solid", fgColor="C6EFCE")))
    ws_.conditional_formatting.add(rng_, CellIsRule(operator="equal", formula=["2"], fill=PatternFill("solid", fgColor="FFEB9C")))
    ws_.conditional_formatting.add(rng_, CellIsRule(operator="equal", formula=["1"], fill=PatternFill("solid", fgColor="F8CBAD")))
ws_r.conditional_formatting.add(f"AE{FIRST}:AE{LAST}", FormulaRule(formula=[f'LEN(AE{FIRST})>0'], font=Font(color="C00000")))
ws_r.conditional_formatting.add(f"Y{FIRST}:Y{LAST}", FormulaRule(formula=[f'ISNUMBER(SEARCH("pending",Y{FIRST}))'], fill=amber))
ws_mr.conditional_formatting.add(f"R{FIRST}:R{LAST}", FormulaRule(formula=[f'LEFT(R{FIRST},6)="REVIEW"'], fill=amber))
ws_l.conditional_formatting.add(f"O{LOG_FIRST}:O{LOG_LAST}", FormulaRule(formula=[f'ISNUMBER(SEARCH("NOT applied",O{LOG_FIRST}))'], fill=red))
ws_g.conditional_formatting.add("O1:O200", FormulaRule(formula=['LEFT(O1,6)="REVIEW"'], fill=amber))

# Sheet order and tab colours
order = ["Read_Me", "Dashboard", "Config", "Employees", "Performance_Input", "Ranking_Calc", "Calibration_Log",
         "Bonus", "Merit", "Budget_Control", "Group_Analysis", "Checks", "Audit_Trail", "Lists"]
wb._sheets = [wb[n] for n in order]
for n, colr in (("Read_Me", "808080"), ("Dashboard", NAVY), ("Config", "BF8F00"), ("Employees", "BF8F00"),
                ("Performance_Input", "BF8F00"), ("Calibration_Log", "BF8F00"), ("Ranking_Calc", TEAL),
                ("Bonus", TEAL), ("Merit", TEAL), ("Budget_Control", TEAL), ("Group_Analysis", TEAL),
                ("Checks", "C00000"), ("Audit_Trail", "7030A0")):
    wb[n].sheet_properties.tabColor = colr
wb.active = 1


def add_sample_calibration():
    """Three illustrative committee entries (filled after IDs are known)."""
    return [
        (date(2027, 1, 25), "EN1005", 4, "Exceptional contribution outside KPIs",
         "Led emergency shutdown recovery (incident report IR-2026-114); not captured in KPI set.",
         "Contribution saved 9 days of downtime.", "Supported", "Approved", "HR Director", date(2027, 1, 26)),
        (date(2027, 1, 25), "EN1012", 5, "Evidence not reflected in score",
         "Manager claims strong performance; no additional evidence supplied.", "Team feedback positive.",
         "Not supported", "Rejected", "", None),
        (date(2027, 1, 25), "EN1020", 3, "Other (explain in evidence)", "", "Awaiting KPI data correction from Finance.",
         "Pending", "Pending", "", None),
    ]


for j, (d, eid, rt, reason, ev, mj, hr, dec, appr, ad) in enumerate(add_sample_calibration()):
    r_ = LOG_FIRST + j
    ws_l[f"B{r_}"], ws_l[f"C{r_}"], ws_l[f"E{r_}"], ws_l[f"G{r_}"] = d, eid, rt, reason
    ws_l[f"H{r_}"], ws_l[f"I{r_}"], ws_l[f"J{r_}"], ws_l[f"K{r_}"] = ev or None, mj, hr, dec
    ws_l[f"L{r_}"], ws_l[f"M{r_}"] = appr or None, ad

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("Saved", OUT)
