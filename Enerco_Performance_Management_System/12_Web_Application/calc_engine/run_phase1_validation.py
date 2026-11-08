"""Phase 1 methodology validation on 120 synthetic employees.

Writes 19_Testing/Phase1_Methodology_Validation_Report.md and CSV extracts.
Run:  python run_phase1_validation.py
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

from enerco_pms.config import BANDS_OPTION_A, get_config, validate_config
from enerco_pms.distribution import analyse_by, analyse_group
from enerco_pms.pipeline import run_cycle
from enerco_pms.rewards import bonus_budget_summary, company_factor, company_score, merit_budget_fit
from enerco_pms.scoring import preliminary_score, rating_for
from enerco_pms.synthetic import generate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "19_Testing"
CSV_DIR = OUT / "phase1_outputs"


def pct(x):
    return f"{x * 100:.1f}%"


def sar(x):
    return f"{x:,.0f}"


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def main():
    cfg = get_config()
    cfg_a = get_config(rating_bands=BANDS_OPTION_A)
    assert not validate_config(cfg), validate_config(cfg)
    emps = generate(120)
    by_id = {e["employee_id"]: e for e in emps}

    rep = ["# Phase 1 Methodology Validation Report",
           "",
           "**Data:** 120 synthetic Enerco employees (seed 2026). No real employee data was used.  ",
           "**Engine:** `12_Web_Application/calc_engine/enerco_pms` (Python reference implementation).  ",
           "**Status:** Generated automatically by `run_phase1_validation.py`. All figures below are outputs of the engine run, not estimates.",
           ""]

    # ------------------------------------------------------------------ 1
    rep += ["## 1. Rating scale alignment test", "",
            "An employee who achieves every KPI target exactly (KPI score 100) and is rated fully proficient "
            "(level 3 = 100) on every competency and behavior:", ""]
    on_target = preliminary_score(100, 100, 100, None, cfg)
    rows = []
    for name, c in (("Approved bands", cfg), ("Option A bands", cfg_a)):
        rows.append([name, on_target, rating_for(on_target, c)[1]])
    rep.append(table(["Band set", "Preliminary score", "Rating"], rows))
    rep += ["", "**Finding F-01:** under the approved bands, fully meeting every expectation produces "
            "**Exceeds Expectations**. See decision D-07 in the Phase 1 Design Specification.", ""]

    # Boundary checks
    rows = []
    for s in (69.99, 69.995, 70.0, 84.99, 84.995, 85.0, 99.99, 99.995, 100.0, 109.99, 109.995, 110.0, 120.0):
        rows.append([s, rating_for(s, cfg)[1], rating_for(s, cfg_a)[1]])
    rep += ["### Boundary values (scores rounded half-up to 2 dp before banding)", "",
            table(["Raw score", "Approved bands", "Option A"], rows), "",
            "Every value maps to exactly one rating: there are no gaps (e.g. 109.995 is not lost between 109.99 and 110).", ""]

    # ------------------------------------------------------------------ 2
    cpf_scenarios = {"Below threshold (company score 68)": {"financial": 65, "operational": 70, "strategic": 72},
                     "On plan (company score 100)": {"financial": 100, "operational": 100, "strategic": 100},
                     "Strong year (company score 112)": {"financial": 118, "operational": 105, "strategic": 108}}
    base_cpf = company_factor(company_score(cpf_scenarios["On plan (company score 100)"], cfg), cfg)
    results = run_cycle(emps, cfg, base_cpf)
    results_a = run_cycle(emps, cfg_a, base_cpf)

    rep += ["## 2. Preliminary rating distribution (no calibration applied)", ""]
    rows = []
    for name, res in (("Approved bands", results), ("Option A bands", results_a)):
        c = Counter(r["preliminary_rating"] for r in res)
        rows.append([name] + [f"{c.get(k, 0)} ({pct(c.get(k, 0) / len(res))})" for k in (5, 4, 3, 2, 1)])
    rows.append(["Guideline", "5%", "15%", "60%", "15%", "5%"])
    rep.append(table(["Band set", "5 Exceptional", "4 Exceeds", "3 Meets", "2 Partially", "1 Does not meet"], rows))
    nocap = run_cycle(emps, get_config(rating_bands=BANDS_OPTION_A, kpi_cap_unapproved_stretch=120.0), base_cpf)
    c = Counter(r["preliminary_rating"] for r in nocap)
    rows.append(["Option A, stretch cap off"] + [f"{c.get(k, 0)} ({pct(c.get(k, 0) / len(nocap))})" for k in (5, 4, 3, 2, 1)])
    rep[-1] = table(["Band set", "5 Exceptional", "4 Exceeds", "3 Meets", "2 Partially", "1 Does not meet"], rows)
    rep += ["", "**Finding F-07:** when no HR-approved stretch value exists, the stretch control caps KPI scores at 100. "
            "That makes rating 5 rare, because an employee then needs mostly level-5 competencies to reach the band. "
            "Setting approved stretch values at objective-setting is therefore a required process step, not an option. "
            "The 'stretch cap off' row shows the effect of removing the control. It is not recommended, because it "
            "rewards targets that were set too low."]
    rep += ["", "The synthetic population is generated around target performance. Under the approved bands, "
            "on-target performers shift into rating 4, which is Finding F-01 seen at population level.", ""]

    # ------------------------------------------------------------------ 3
    recs = [{**r, "department": by_id[r["employee_id"]]["department"], "grade": by_id[r["employee_id"]]["grade"],
             "rating": r["preliminary_rating"]} for r in results_a]
    company = analyse_group([r["rating"] for r in recs], cfg_a)
    rep += ["## 3. Guided distribution analysis (Option A bands, company level)", "",
            f"Group size {company['n']}, status **{company['status']}**.", ""]
    rows = [[r["rating"], r["count"], pct(r["actual_pct"]), pct(r["target_pct"]), f"{r['variance_pp']:+.1f} pp",
             f"{r['expected_range'][0]}-{r['expected_range'][1]}", "FLAG" if r["flag"] else ""] for r in company["rows"]]
    rep.append(table(["Rating", "Count", "Actual", "Guideline", "Variance", "Expected range (90%)", "Flag"], rows))
    rep += ["", "### By department", ""]
    rows = []
    for g, a in analyse_by(recs, "department", cfg_a).items():
        flags = [str(r["rating"]) for r in a["rows"] if r["flag"]]
        rows.append([g, a["n"], a["status"], ", ".join(flags) or "-",
                     pct(a["prob_no_exceptional"])])
    rep.append(table(["Department", "n", "Comparison status", "Ratings outside range", "P(no 'Exceptional' by chance)"], rows))
    rep += ["", "**Finding F-02:** in a group of 20 with a 5% guideline, the chance of having nobody rated "
            f"Exceptional is {pct(0.95 ** 20)}. Small groups must not be forced to fill every category. The engine "
            "only flags a variance when the count falls outside the binomial range, and it never changes a rating.", ""]

    # ------------------------------------------------------------------ 4
    rep += ["## 4. Calibration override test", ""]
    first_4 = next(r for r in results_a if r["preliminary_rating"] == 4 and by_id[r["employee_id"]]["scenario"] == "standard")
    overrides = {first_4["employee_id"]: 3}
    cal = run_cycle(emps, cfg_a, base_cpf, final_rating_overrides=overrides)
    changed = [r for r in cal if r["calibrated"]]
    c0 = next(r for r in results_a if r["employee_id"] == first_4["employee_id"])
    c1 = changed[0]
    rep.append(table(["Employee", "Preliminary score", "Preliminary rating", "Final rating", "Bonus before", "Bonus after",
                      "Merit % before", "Merit % after"],
                     [[c1["employee_id"], c1["preliminary_score"], c1["preliminary_rating"], c1["final_rating"],
                       sar(c0["bonus"]["bonus"]), sar(c1["bonus"]["bonus"]), pct(c0["merit"]["merit_pct"]),
                       pct(c1["merit"]["merit_pct"])]]))
    rep += ["", f"Only {len(changed)} record changed. The preliminary score is retained beside the final rating "
            "and rewards follow the final calibrated rating.", ""]

    # ------------------------------------------------------------------ 5
    rep += ["## 5. Annual bonus scenarios (Option A bands, illustrative target bonus % by grade)", ""]
    rows = []
    for name, comps in cpf_scenarios.items():
        cs = company_score(comps, cfg_a)
        f = company_factor(cs, cfg_a)
        res = run_cycle(emps, cfg_a, f)
        summ = bonus_budget_summary([r["bonus"] for r in res], None)
        rows.append([name, cs, f, sar(summ["target_bonus_total"]), sar(summ["calculated_liability"]),
                     pct(summ["calculated_liability"] / summ["target_bonus_total"]) if summ["target_bonus_total"] else "-"])
    rep.append(table(["Scenario", "Company score", "CPF (step)", "Target bonus pool (SAR)", "Calculated liability (SAR)", "Liability / target"], rows))
    lin = [(s, company_factor(s, get_config(company_payout_method="linear"))) for s in (69.99, 70, 75, 79.99, 80, 95, 105, 110, 115)]
    rep += ["", "Step vs. linear company payout factor (both supported by configuration):", "",
            table(["Company score", "Step factor", "Linear factor"],
                  [[s, company_factor(s, cfg), f] for s, f in lin]),
            "",
            "**Finding F-03:** the step table creates cliffs. A company score of 79.99 pays 0.50 and 80.00 pays 0.75, "
            "a 50% jump in the bonus pool for 0.01 points. Linear interpolation is offered as an option for decision D-13.", ""]
    exp_mult = sum(cfg["guided_distribution"][k] * cfg["bonus_multipliers"][k] for k in range(1, 6))
    rep += [f"**Finding F-04:** if final ratings matched the 5/15/60/15/5 guideline exactly, the average individual "
            f"multiplier would be **{exp_mult:.4f}**, so at CPF 1.00 the pool would be {exp_mult * 100:.2f}% of the target bonus pool. "
            "Finance can use this figure for accrual planning.", ""]

    # Bonus edge cases
    rows = []
    for r in results_a:
        e = by_id[r["employee_id"]]
        if e["scenario"] != "standard":
            b = r["bonus"]
            rows.append([e["employee_id"], e["scenario"], b.get("proration", "-"), sar(b["bonus"]),
                         b.get("reason") or "", ", ".join(b["flags"]) or ""])
    rep += ["### Bonus eligibility edge cases", "",
            table(["Employee", "Scenario", "Proration", "Bonus (SAR)", "Reason", "Flags"], rows), ""]

    # ------------------------------------------------------------------ 6
    rep += ["## 6. Merit budget simulation (Option A ratings, illustrative matrix)", ""]
    pairs = [(by_id[r["employee_id"]], r["preliminary_rating"]) for r in results_a]
    rows = []
    for b in (0.02, 0.03, 0.04):
        m = merit_budget_fit(pairs, cfg_a, b)
        rows.append([pct(b), sar(m["eligible_monthly_payroll"]), sar(m["budget_monthly"] * 12), sar(m["matrix_cost_monthly"] * 12),
                     f"{m['matrix_cost_pct_of_payroll']:.2f}%", sar(m["variance_monthly"] * 12), m["scale_to_fit"]])
    rep.append(table(["Budget", "Eligible monthly payroll", "Annual budget (SAR)", "Annual matrix cost (SAR)", "Matrix cost % payroll",
                      "Annual variance (SAR)", "Uniform scale to fit"], rows))
    rep += ["", "**Finding F-05:** the illustrative matrix has a fixed cost that depends on the rating mix and compa-ratio "
            "mix. It does not automatically equal any budget. The engine reports the uniform scale factor that would "
            "fit each budget. Applying it is an executive decision, and ratings are never changed.", ""]

    # Expected matrix cost if final ratings followed the guideline exactly, using the actual compa-ratio mix.
    elig_pay = exp_cost = 0.0
    for r in results_a:
        m = r["merit"]
        if m["status"] in ("NOT_ELIGIBLE", "JOINED_AFTER_CUTOFF", "LEAVER"):
            continue
        sal = by_id[r["employee_id"]]["monthly_basic"]
        elig_pay += sal
        exp_cost += sal * sum(p * cfg_a["merit_matrix"][k][m["cr_band"]] for k, p in cfg_a["guided_distribution"].items())
    rep += [f"**Finding F-06:** even if ratings followed the 5/15/60/15/5 guideline exactly, the illustrative matrix "
            f"would cost about **{exp_cost / elig_pay * 100:.2f}% of eligible payroll** with this compa-ratio mix. "
            "That is below a 2%, 3% or 4% budget, so the matrix percentages have to be calibrated to the approved budget "
            "before they can be used (decision D-16).", ""]

    merit_rows = [r["merit"] for r in results_a]
    by_status = Counter(m["status"] for m in merit_rows)
    rep += ["### Merit status counts", "", table(["Status", "Employees"], sorted(by_status.items())), ""]
    rows = [[m["employee_id"], by_id[m["employee_id"]]["scenario"], m["compa_ratio"], m["cr_band"], pct(m["merit_pct"]),
             m["new_compa_ratio"], m["status"], ", ".join(m["flags"])]
            for m in merit_rows if m["status"] != "PROPOSED" or m["flags"]]
    rep += ["### Merit exceptions requiring review", "",
            table(["Employee", "Scenario", "CR", "CR band", "Merit %", "New CR", "Status", "Flags"], rows), "",
            "Increases that would take salary above range maximum are **flagged for review, not truncated**.", ""]

    cost_by = defaultdict(float)
    for r in results_a:
        cost_by[by_id[r["employee_id"]]["grade"]] += r["merit"]["increase"] * 12
    rep += ["### Annual merit cost by grade (matrix as illustrated)", "",
            table(["Grade", "Annual cost (SAR)"], [[g, sar(v)] for g, v in sorted(cost_by.items())]), ""]

    # ------------------------------------------------------------------ 7
    qa = Counter(f for r in results_a for f in r["qa_flags"])
    rep += ["## 7. KPI quality-control flags raised", "", table(["Flag", "KPIs/employees affected"], sorted(qa.items())), "",
            "KPI scores with unverified evidence, unreliable data or unapproved target changes are capped at 100. "
            "KPIs above target need an HR-approved stretch value to score above 100. Targets that are not harder "
            "than the baseline are flagged for HR QA.", ""]

    (OUT / "Phase1_Methodology_Validation_Report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_DIR / "synthetic_employees.csv", "w", newline="", encoding="utf-8") as f:
        cols = [k for k in emps[0] if k not in ("kpis", "competency_levels", "behavior_levels")] + ["exit_date", "exit_type"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(emps)
    with open(CSV_DIR / "phase1_results_option_a.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["employee_id", "kpi_score", "competency_score", "behavior_score", "preliminary_score",
                    "preliminary_rating", "final_rating", "bonus_sar", "merit_pct", "merit_increase_monthly",
                    "merit_status", "qa_flags"])
        for r in results_a:
            w.writerow([r["employee_id"], round(r["kpi_score"], 2), round(r["competency_score"], 2),
                        round(r["behavior_score"], 2), r["preliminary_score"], r["preliminary_rating"],
                        r["final_rating"], r["bonus"]["bonus"], r["merit"]["merit_pct"], r["merit"]["increase"],
                        r["merit"]["status"], ";".join(r["qa_flags"])])
    print("Report written:", OUT / "Phase1_Methodology_Validation_Report.md")


if __name__ == "__main__":
    main()
