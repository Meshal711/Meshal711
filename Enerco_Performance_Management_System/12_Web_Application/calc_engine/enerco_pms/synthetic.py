"""Deterministic synthetic Enerco workforce for development and testing.

No real employee data. Names are omitted; employees are identified by ID only.
"""

import random
from datetime import date, timedelta

DEPARTMENTS = {
    "D01": ("Operations", "OPS"), "D02": ("Engineering", "ENG"), "D03": ("Projects", "PRJ"),
    "D04": ("Finance", "FIN"), "D05": ("Human Resources", "HRM"), "D06": ("Supply Chain", "SCM"),
    "D07": ("HSE", "HSE"), "D08": ("Commercial", "COM"),
}
# Department -> job families present
FAMILIES = {
    "D01": ["Operations", "Maintenance"], "D02": ["Engineering"], "D03": ["Project Management", "Engineering"],
    "D04": ["Finance"], "D05": ["Human Resources"], "D06": ["Supply Chain"], "D07": ["HSE"],
    "D08": ["Commercial"],
}
# Grade -> (monthly basic midpoint SAR, career level, target bonus %)  ILLUSTRATIVE ONLY
GRADES = {
    "G05": (6500, "Individual Contributor", 0.05), "G06": (8000, "Individual Contributor", 0.06),
    "G07": (9800, "Individual Contributor", 0.08), "G08": (12000, "Individual Contributor", 0.10),
    "G09": (14700, "Supervisor", 0.10), "G10": (18000, "Manager", 0.12),
    "G11": (22000, "Manager", 0.15), "G12": (27000, "Senior Management", 0.20),
    "G13": (33000, "Senior Management", 0.25),
}
RANGE_SPREAD = 0.40  # max/min - 1, so min = mid/1.2, max = mid*1.4/1.2
GRADE_WEIGHTS = [10, 16, 18, 16, 12, 10, 8, 6, 4]

COMPETENCIES = ["C01", "C02", "C03", "C04", "C05"]
BEHAVIORS = ["V01", "V02", "V03", "V04"]


def salary_range(grade):
    mid = GRADES[grade][0]
    mn = mid * 2 / (2 + RANGE_SPREAD)
    mx = mn * (1 + RANGE_SPREAD)
    return round(mn, 2), float(mid), round(mx, 2)


def _level_from(ability, rng):
    x = 3 + ability * 1.1 + rng.gauss(0, 0.45)
    return int(min(5, max(1, round(x))))


def _make_kpis(ability, rng, evidence_ok, n):
    kpis = []
    weights = [rng.uniform(0.6, 1.4) for _ in range(n)]
    s = sum(weights)
    weights = [round(w / s, 4) for w in weights]
    weights[-1] = round(1 - sum(weights[:-1]), 4)
    types = ["higher_is_better", "higher_is_better", "lower_is_better", "binary", "milestone"]
    for i in range(n):
        mt = types[i % len(types)]
        perf = ability * 0.08 + rng.gauss(0, 0.07)   # relative deviation from target
        k = {"kpi_id": f"K{i+1}", "measure_type": mt, "weight": weights[i],
             "evidence_verified": evidence_ok, "data_quality": "verified"}
        if mt == "higher_is_better":
            tg = rng.choice([100, 250, 1000, 5_000_000])
            k.update(baseline=tg * 0.95, threshold=tg * 0.85, target=tg, actual=tg * (1 + perf))
            if rng.random() < 0.5:
                k.update(stretch=tg * 1.15, stretch_approved=True)
        elif mt == "lower_is_better":
            tg = rng.choice([2.0, 10.0, 48.0])
            k.update(baseline=tg * 1.05, threshold=tg * 1.2, target=tg, actual=tg * (1 - perf))
            if rng.random() < 0.5:
                k.update(stretch=tg * 0.85, stretch_approved=True)
        elif mt == "binary":
            k.update(actual=1 if rng.random() < 0.75 + ability * 0.15 else 0)
        else:
            k.update(baseline=0.8, threshold=0.7, target=1.0, actual=min(1.0, max(0.0, 0.92 + perf)))
        kpis.append(k)
    return kpis


def generate(n=120, seed=2026):
    rng = random.Random(seed)
    emps = []
    dept_ids = list(DEPARTMENTS)
    for i in range(n):
        dept = dept_ids[i % len(dept_ids)] if i < 16 else rng.choices(dept_ids, [22, 18, 14, 10, 6, 10, 8, 12])[0]
        grade = rng.choices(list(GRADES), GRADE_WEIGHTS)[0]
        mid, level, tgt = GRADES[grade]
        mn, mid, mx = salary_range(grade)
        cr = rng.uniform(0.82, 1.18)
        emp = {
            "employee_id": f"EN{1000 + i}",
            "legal_entity": "ENERCO",
            "department_id": dept,
            "department": DEPARTMENTS[dept][0],
            "job_family": rng.choice(FAMILIES[dept]),
            "grade": grade,
            "career_level": level,
            "nationality_group": "Saudi" if rng.random() < 0.65 else "Expatriate",
            "employment_date": (date(2014, 1, 1) + timedelta(days=rng.randint(0, 11 * 365))).isoformat(),
            "employment_status": "Active",
            "contract_type": rng.choice(["Indefinite", "Fixed-term"]),
            "monthly_basic": round(mid * cr, -1),
            "monthly_fixed_allowances": round(mid * cr * 0.35, -1),
            "range_min": mn, "range_mid": mid, "range_max": mx,
            "target_bonus_pct": tgt,
            "bonus_eligible": True,
            "merit_eligible": True,
            "unpaid_leave_days": 0,
            "scenario": "standard",
        }
        emps.append(emp)

    # Deliberate edge cases (test coverage requirements, Master Prompt section 18).
    def tag(idx, **kw):
        emps[idx].update(kw)

    tag(3, employment_date="2026-03-15", scenario="new_joiner_partial_year")
    tag(7, employment_date="2026-11-01", scenario="new_joiner_after_cutoff")
    tag(11, employment_date="2026-10-20", scenario="joiner_below_min_service")
    tag(15, exit_date="2026-08-31", exit_type="resignation", employment_status="Resigned", scenario="leaver_resignation")
    tag(19, exit_date="2026-06-30", exit_type="termination", employment_status="Terminated", scenario="leaver_termination")
    tag(23, unpaid_leave_days=45, scenario="unpaid_leave")
    tag(27, monthly_basic=round(emps[27]["range_max"] * 1.03, -1), scenario="salary_above_range_max")
    tag(31, monthly_basic=round(emps[31]["range_max"] * 0.995, -1), scenario="salary_near_range_max")
    tag(35, monthly_basic=round(emps[35]["range_min"] * 0.92, -1), scenario="salary_below_range_min")
    tag(39, bonus_eligible=False, scenario="contractually_not_bonus_eligible")
    tag(43, merit_eligible=False, scenario="not_merit_eligible")
    tag(47, scenario="incomplete_evidence")
    tag(51, scenario="unapproved_target_change")
    tag(55, scenario="target_below_baseline")

    # Performance inputs
    for e in emps:
        ability = rng.gauss(0, 1)
        evidence_ok = e["scenario"] != "incomplete_evidence"
        e["kpis"] = _make_kpis(ability, rng, evidence_ok, rng.randint(3, 6))
        if e["scenario"] == "unapproved_target_change":
            e["kpis"][0].update(target_changed=True, target_change_approved=False)
        if e["scenario"] == "target_below_baseline":
            k = e["kpis"][0]
            if k["measure_type"] == "higher_is_better":
                k["baseline"] = k["target"] * 1.10
        e["competency_levels"] = [_level_from(ability, rng) for _ in COMPETENCIES]
        e["behavior_levels"] = [_level_from(ability * 0.6, rng) for _ in BEHAVIORS]
    return emps
