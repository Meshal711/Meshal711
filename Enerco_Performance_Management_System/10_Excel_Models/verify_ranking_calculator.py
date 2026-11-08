"""Independent verification of the Excel calculator.

1. Recalculates the workbook with LibreOffice (headless) so every formula is evaluated.
2. Re-implements the methodology in plain Python from the INPUT cells only.
3. Compares every employee's score, ranks, ratings, bonus and merit to the Excel results.
4. Scans every sheet for Excel error values.

Usage: python verify_ranking_calculator.py [path-to-xlsx]
Writes 19_Testing/Excel_Ranking_Calculator_Verification.md
"""

import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "Enerco_Performance_Ranking_BellCurve_Calculator.xlsx"
REPORT = HERE.parent / "19_Testing" / "Excel_Ranking_Calculator_Verification.md"
FIRST, LAST = 5, 304


def recalc(path):
    out = Path(tempfile.mkdtemp())
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(out), str(path)],
                   check=True, capture_output=True, timeout=300)
    return out / path.name


def d(v):
    return v.date() if isinstance(v, datetime) else v


def name_value(wb, name):
    dest = list(wb.defined_names[name].destinations)[0]
    ws = wb[dest[0]]
    ref = dest[1].replace("$", "")
    cells = ws[ref]
    if isinstance(cells, tuple):
        flat = [c.value for row in (cells if isinstance(cells[0], tuple) else (cells,)) for c in row]
        return flat
    return cells.value


def rhu(x, dp=2):
    """ROUND half-up on the 15-significant-digit value, as Excel and LibreOffice do."""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(format(x, '.15g')).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP))


def excel_round(x, dp=0):
    return rhu(x, dp)


def python_model(inp):
    """Independent implementation from input cells (formula-free workbook)."""
    N = lambda n: name_value(inp, n)
    w_kpi, w_comp, w_beh = N("W_KPI"), N("W_COMP"), N("W_BEH")
    kpi_max, cap_noev = N("KPI_MAX"), N("KPI_CAP_NOEVID")
    prof = N("PROF_SCORES")
    band_lower, band_rating = N("BAND_LOWER"), N("BAND_RATING")
    dist = {r: N(f"DIST_{r}") for r in range(1, 6)}
    mode, basis, min_group, max_adj = N("CURVE_MODE"), N("COMP_BASIS"), N("MIN_GROUP"), N("MAX_ADJ")
    conf_down, conf_up = N("CONFIRM_DOWN"), N("CONFIRM_UP")
    mult = N("BONUS_MULT")
    cs_w, cs_s = N("CS_WEIGHTS"), N("CS_SCORES")
    thr, fac = N("PAY_THR"), N("PAY_FAC")
    cstart, cend = d(N("CYCLE_START")), d(N("CYCLE_END"))
    min_service, months = N("MIN_SERVICE"), N("BONUS_MONTHS")
    budget, apply_ff = N("BONUS_BUDGET"), N("APPLY_FF")
    merit_pct, scale_yes, merit_max = N("MERIT_BUDGET_PCT"), N("SCALE_TO_BUDGET"), N("MERIT_MAX")
    cutoff = d(N("MERIT_CUTOFF"))
    cr_lower, matrix_flat = N("CR_LOWER"), N("MERIT_MATRIX")
    matrix = {5 - i: matrix_flat[i * 5:(i + 1) * 5] for i in range(5)}
    g_list, g_min, g_mid, g_max, g_tgt = (N(x) for x in ("GRADE_LIST", "GRADE_MIN", "GRADE_MID", "GRADE_MAX", "GRADE_TGT"))
    grades = {g: (mn, md, mx, t) for g, mn, md, mx, t in zip(g_list, g_min, g_mid, g_max, g_tgt) if g}

    company = rhu(sum(a * b for a, b in zip(cs_w, cs_s)), 2)
    if N("PAY_METHOD") == "Step":
        cpf = [f for t, f in zip(thr, fac) if company >= t][-1]
    elif company < thr[1]:
        cpf = 0.0
    elif company >= thr[-1]:
        cpf = fac[-1]
    else:
        i = max(j for j, t in enumerate(thr) if company >= t)
        cpf = rhu(fac[i] + (fac[i + 1] - fac[i]) * (company - thr[i]) / (thr[i + 1] - thr[i]), 4)

    E, P = inp["Employees"], inp["Performance_Input"]
    emps = []
    for r in range(FIRST, LAST + 1):
        eid = E[f"A{r}"].value
        if not eid:
            continue
        ev = P[f"V{r}"].value
        caps = kpi_max if ev == "Yes" else min(kpi_max, cap_noev)
        wsum = wk = 0.0
        for k in range(5):
            wv = P.cell(row=r, column=3 + 2 * k).value
            av = P.cell(row=r, column=4 + 2 * k).value
            wv = wv or 0
            sc = 0 if av is None else min(caps, max(0, av * 100))
            wsum += wv
            wk += wv * sc
        kpi = 0 if wsum == 0 else wk / wsum
        comp_l = [P.cell(row=r, column=c).value for c in range(13, 18)]
        beh_l = [P.cell(row=r, column=c).value for c in range(18, 22)]
        conv = lambda ls: (sum(prof[int(x) - 1] for x in ls if isinstance(x, (int, float))) /
                           max(1, len([x for x in ls if isinstance(x, (int, float))])))
        comp, beh = conv(comp_l), conv(beh_l)
        score = rhu(kpi * w_kpi + comp * w_comp + beh * w_beh, 2)
        srat = max(rt for lo, rt in zip(band_lower, band_rating) if score >= lo)
        level, grade = E[f"F{r}"].value, E[f"G{r}"].value
        emps.append({"row": r, "id": eid, "seq": r - 4, "level": level, "grade": grade,
                     "group": grade if basis == "Grade" else level, "kpi": kpi, "comp": comp, "beh": beh,
                     "score": score, "srat": srat, "hire": d(E[f"H{r}"].value), "exit": d(E[f"I{r}"].value),
                     "unpaid": E[f"J{r}"].value or 0, "basic": E[f"K{r}"].value,
                     "bonus_el": E[f"L{r}"].value, "merit_el": E[f"M{r}"].value})

    # Ranks & curve
    for e in emps:
        grp = [x for x in emps if x["group"] == e["group"]]
        n = len(grp)
        rank = sum(1 for x in grp if x["score"] > e["score"]) + sum(1 for x in grp if x["score"] == e["score"] and x["seq"] < e["seq"]) + 1
        e["n"], e["rank"] = n, rank
        e["crank"] = sum(1 for x in emps if x["score"] > e["score"]) + sum(1 for x in emps if x["score"] == e["score"] and x["seq"] < e["seq"]) + 1
        if n < min_group:
            curve = e["srat"]
        else:
            c5 = excel_round(n * dist[5]); c4 = excel_round(n * (dist[5] + dist[4]))
            c3 = excel_round(n * (dist[5] + dist[4] + dist[3])); c2 = excel_round(n * (dist[5] + dist[4] + dist[3] + dist[2]))
            curve = 5 if rank <= c5 else 4 if rank <= c4 else 3 if rank <= c3 else 2 if rank <= c2 else 1
        e["curve"] = curve
        q = e["srat"]
        prop = q if mode == "Guided" else curve if mode == "Forced" else q + max(-max_adj, min(max_adj, curve - q))
        sysr = q if (prop < q and conf_down == "Yes") or (prop > q and conf_up == "Yes") else prop
        e["system"] = sysr

    # Calibration log (latest effective entry wins)
    L = inp["Calibration_Log"]
    by_id = {e["id"]: e for e in emps}
    for e in emps:
        e["final"] = e["system"]
    for r in range(5, 205):
        eid = L[f"C{r}"].value
        if not eid or eid not in by_id:
            continue
        if L[f"K{r}"].value == "Approved" and L[f"H{r}"].value and L[f"L{r}"].value and isinstance(L[f"E{r}"].value, (int, float)):
            by_id[eid]["final"] = int(L[f"E{r}"].value)

    # Bonus
    cycle_days = (cend - cstart).days + 1
    liability = 0.0
    for e in emps:
        end = cend if e["exit"] is None else min(e["exit"], cend)
        days = max(0, (end - max(e["hire"], cstart)).days + 1 - e["unpaid"])
        pr = 0 if days < min_service else days / cycle_days
        tgt = grades[e["grade"]][3]
        e["bonus_calc"] = rhu(e["basic"] * months * tgt * cpf * mult[e["final"] - 1] * pr, 2) if e["bonus_el"] == "Yes" else 0.0
        liability += e["bonus_calc"]
    ff = budget / liability if apply_ff == "Yes" and liability > budget and liability > 0 else 1
    for e in emps:
        e["bonus"] = rhu(e["bonus_calc"] * ff, 2)

    # Merit
    unscaled = payroll = 0.0
    for e in emps:
        mn, md, mx, _ = grades[e["grade"]]
        cr = rhu(e["basic"] / md * 100, 2)
        band = max(i for i, lo in enumerate(cr_lower) if cr >= lo)
        e["cr"], e["mpct_matrix"] = cr, matrix[e["final"]][band]
        e["merit_el_calc"] = e["merit_el"] == "Yes" and e["hire"] < cutoff and e["exit"] is None
        if e["merit_el_calc"]:
            unscaled += e["basic"] * e["mpct_matrix"] * 12
            payroll += e["basic"] * 12
    fit = 0 if unscaled == 0 else payroll * merit_pct / unscaled
    scale = fit if scale_yes == "Yes" else 1
    for e in emps:
        e["merit_pct"] = min(merit_max, e["mpct_matrix"] * scale) if e["merit_el_calc"] else 0
        e["merit_inc"] = rhu(e["basic"] * e["merit_pct"], 2)
    return emps, {"company": company, "cpf": cpf, "ff": ff, "liability": liability, "scale": scale}


SCENARIOS = [
    ("Forced curve, Grade comparison groups", {"CURVE_MODE": "Forced", "COMP_BASIS": "Grade"}),
    ("Guided mode (score bands only)", {"CURVE_MODE": "Guided"}),
    ("Hybrid, all curve changes auto-applied, max adjustment 2", {"CONFIRM_DOWN": "No", "MAX_ADJ": 2}),
    ("Approved alternative bands 110/100/85/70", {"BAND_LOWER": [0, 70, 85, 100, 110]}),
    ("Step payout, weak company year (score ~78)", {"PAY_METHOD": "Step", "CS_SCORES": [75, 80, 82]}),
    ("Bonus budget 1.5M with funding factor; merit scaled to 4% budget",
     {"BONUS_BUDGET": 1_500_000, "APPLY_FF": "Yes", "SCALE_TO_BUDGET": "Yes", "MERIT_BUDGET_PCT": 0.04}),
    ("Weights 60/30/10, min group 20", {"W_KPI": 0.6, "W_COMP": 0.3, "MIN_GROUP": 20}),
]


def set_name(wb, name, value):
    dest = list(wb.defined_names[name].destinations)[0]
    ws = wb[dest[0]]
    cells = ws[dest[1].replace("$", "")]
    if isinstance(value, list):
        flat = [c for row in (cells if isinstance(cells[0], tuple) else (cells,)) for c in row]
        for c, v in zip(flat, value):
            c.value = v
    else:
        cells.value = value


def compare(path):
    calc_path = recalc(path)
    out = load_workbook(calc_path, data_only=True)
    emps, glob = python_model(load_workbook(path))
    R, B, M = out["Ranking_Calc"], out["Bonus"], out["Merit"]
    cols = [("P", R, "score", 0.005), ("Q", R, "srat", 0), ("S", R, "rank", 0), ("V", R, "curve", 0),
            ("X", R, "system", 0), ("AA", R, "final", 0), ("P", B, "bonus", 0.01), ("M", M, "merit_pct", 1e-9),
            ("N", M, "merit_inc", 0.01)]
    mism = sum(1 for e in emps for col, ws, key, tol in cols
               if ws[f"{col}{e['row']}"].value is None or abs(float(ws[f"{col}{e['row']}"].value) - float(e[key])) > tol)
    errs = sum(1 for ws in out.worksheets for row in ws.iter_rows() for c in row
               if isinstance(c.value, str) and (c.value.startswith("#") and c.value.endswith(("!", "?", "A")) or c.value.startswith("Err:")))
    dist = [sum(1 for e in emps if e["final"] == r) for r in (5, 4, 3, 2, 1)]
    bc = out["Budget_Control"]
    summary = {"dist": dist, "bonus": sum(e["bonus"] for e in emps), "merit": sum(e["merit_inc"] for e in emps) * 12,
               "cpf": glob["cpf"], "ff": glob["ff"], "scale": glob["scale"]}
    shutil.rmtree(calc_path.parent, ignore_errors=True)
    return mism, errs, summary, len(emps) * len(cols)


def run_scenarios():
    rows = []
    tmp = Path(tempfile.mkdtemp())
    for label, changes in SCENARIOS:
        wb = load_workbook(SRC)
        for k, v in changes.items():
            set_name(wb, k, v)
        path = tmp / SRC.name
        wb.save(path)
        rows.append((label, *compare(path)))
    shutil.rmtree(tmp, ignore_errors=True)
    return rows


def main():
    calc_path = recalc(SRC)
    out = load_workbook(calc_path, data_only=True)
    inp = load_workbook(SRC)  # input values (formulas unevaluated)
    emps, glob = python_model(inp)

    R, B, M = out["Ranking_Calc"], out["Bonus"], out["Merit"]
    fields = [("Final score", "P", R, "score", 0.005), ("Score-based rating", "Q", R, "srat", 0),
              ("Group size", "R", R, "n", 0), ("Rank in group", "S", R, "rank", 0), ("Curve rating", "V", R, "curve", 0),
              ("System rating", "X", R, "system", 0), ("FINAL rating", "AA", R, "final", 0),
              ("Company rank", "AC", R, "crank", 0), ("Final bonus", "P", B, "bonus", 0.01),
              ("Compa-ratio", "H", M, "cr", 0.005), ("Merit %", "M", M, "merit_pct", 1e-9),
              ("Monthly merit increase", "N", M, "merit_inc", 0.01)]
    mismatches = []
    for e in emps:
        for label, col, ws, key, tol in fields:
            xv = ws[f"{col}{e['row']}"].value
            if xv is None or abs(float(xv) - float(e[key])) > tol:
                mismatches.append((e["id"], label, xv, e[key]))

    errors = []
    for ws in out.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("#") and c.value.rstrip("!?/0").upper() in (
                        "#N/A", "#VALUE", "#REF", "#NAME", "#DIV", "#NUM", "#NULL") or (isinstance(c.value, str) and c.value in (
                        "#N/A", "#VALUE!", "#REF!", "#NAME?", "#DIV/0!", "#NUM!", "#NULL!", "Err:502", "Err:504", "Err:508")):
                    errors.append(f"{ws.title}!{c.coordinate} = {c.value}")

    D, BC, K = out["Dashboard"], out["Budget_Control"], out["Checks"]
    lines = ["# Excel Ranking & Bell Curve Calculator – Verification Report", "",
             f"**Workbook:** `10_Excel_Models/{SRC.name}`  ",
             f"**Run:** {date.today().isoformat()} · recalculated with LibreOffice Calc (headless) · compared with an independent Python implementation (`verify_ranking_calculator.py`) that reads only the input cells.  ",
             f"**Employees checked:** {len(emps)} (synthetic) · **Fields compared per employee:** {len(fields)} · **Comparisons:** {len(emps) * len(fields)}", "",
             "## Result", "",
             f"- Mismatches between Excel and independent calculation: **{len(mismatches)}**",
             f"- Excel error values (#N/A, #VALUE!, #REF!, #NAME?, #DIV/0!, …) in any sheet: **{len(errors)}**",
             f"- Company score {glob['company']} → company factor Excel {out['Config'][list(inp.defined_names['CPF'].destinations)[0][1].replace('$','')].value} / Python {glob['cpf']}",
             f"- Model checks overall status (Checks sheet): **{K['D24'].value}**", ""]
    if mismatches:
        lines += ["| Employee | Field | Excel | Python |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d_} |" for a, b, c, d_ in mismatches[:50]]
    if errors:
        lines += ["", "Errors:", ""] + [f"- {x}" for x in errors[:50]]
    lines += ["", "## Dashboard snapshot (sample data, default configuration)", "",
              "| Rating | Guideline % | Score-based # | Final # | Final % |", "|---|---|---|---|---|"]
    for r in range(12, 17):
        lines.append(f"| {D[f'A{r}'].value} – {D[f'B{r}'].value} | {D[f'C{r}'].value:.0%} | {D[f'E{r}'].value} | {D[f'F{r}'].value} | {D[f'G{r}'].value:.1%} |")
    lines += ["", "| Budget item | Value |", "|---|---|"]
    for r in range(4, 30):
        if BC[f"A{r}"].value and BC[f"B{r}"].value is not None:
            v = BC[f"B{r}"].value
            lines.append(f"| {BC[f'A{r}'].value} | {v:,.4f} |" if isinstance(v, float) and abs(v) < 10 else
                         f"| {BC[f'A{r}'].value} | {v:,.0f} |" if isinstance(v, (int, float)) else f"| {BC[f'A{r}'].value} | {v} |")
    lines += ["", "## Checks sheet", "", "| # | Check | Result | Status |", "|---|---|---|---|"]
    for r in range(5, 23):
        if K[f"B{r}"].value:
            lines.append(f"| {K[f'A{r}'].value} | {K[f'B{r}'].value} | {K[f'C{r}'].value} | {K[f'D{r}'].value} |")
    lines += ["", "WARN items are expected with the sample data: they show the controls working (a missing rating, curve "
              "reductions awaiting committee confirmation, range-max review cases, bonus budget pressure)."]
    sc = run_scenarios()
    lines += ["", "## Configuration scenarios (each recalculated in LibreOffice and re-verified independently)", "",
              "| Scenario | Comparisons | Mismatches | Errors | Final 5/4/3/2/1 | Company factor | Funding factor | Merit scale | Bonus (SAR) | Merit (SAR/yr) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for label, mism, errs, sm, n in sc:
        lines.append(f"| {label} | {n} | {mism} | {errs} | {'/'.join(map(str, sm['dist']))} | {sm['cpf']} | "
                     f"{sm['ff']:.4f} | {sm['scale']:.4f} | {sm['bonus']:,.0f} | {sm['merit']:,.0f} |")
    total_bad = sum(x[1] + x[2] for x in sc)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.rmtree(calc_path.parent, ignore_errors=True)
    print(f"mismatches={len(mismatches)} errors={len(errors)} scenario_issues={total_bad} -> {REPORT}")
    return 1 if mismatches or errors or total_bad else 0


if __name__ == "__main__":
    sys.exit(main())
