"""Annual bonus and merit increase engines.

Ratings are inputs only. Neither engine changes a rating to fit a budget:
budget pressure is handled by an explicit, approved funding factor that applies
to everyone equally and is recorded in the audit trail.
"""

from datetime import date

from .scoring import round_half_up


# ---------------------------------------------------------------------------
# Company performance factor
# ---------------------------------------------------------------------------

def company_score(components, cfg):
    """components: {'financial': score, 'operational': score, 'strategic': score} on the 0..120 scale."""
    w = cfg["company_scorecard_weights"]
    return round_half_up(sum(components[k] * w[k] for k in w), 2)


def company_factor(score, cfg):
    table = cfg["company_payout_table"]  # descending lower bounds
    if cfg["company_payout_method"] == "step":
        for lower, factor in table:
            if score >= lower:
                return factor
    # Linear: interpolate between the finite table points; below lowest finite point -> 0.
    pts = sorted((lo, f) for lo, f in table if lo != float("-inf"))
    if score < pts[0][0]:
        return 0.0
    if score >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= score < x1:
            return round_half_up(y0 + (y1 - y0) * (score - x0) / (x1 - x0), 4)
    raise AssertionError("unreachable")


# ---------------------------------------------------------------------------
# Eligibility & proration
# ---------------------------------------------------------------------------

def _d(s):
    return s if isinstance(s, date) else date.fromisoformat(s)


def eligible_days(emp, cfg):
    """Days in the cycle the employee was in active, bonus-eligible employment, net of unpaid leave."""
    cs, ce = _d(cfg["cycle_start"]), _d(cfg["cycle_end"])
    start = max(cs, _d(emp["employment_date"]))
    end = min(ce, _d(emp["exit_date"])) if emp.get("exit_date") else ce
    if end < start:
        return 0
    return max(0, (end - start).days + 1 - emp.get("unpaid_leave_days", 0))


def bonus_proration(emp, cfg):
    cycle_days = (_d(cfg["cycle_end"]) - _d(cfg["cycle_start"])).days + 1
    days = eligible_days(emp, cfg)
    if days < cfg["bonus_min_service_days"]:
        return 0.0, "BELOW_MIN_SERVICE"
    return days / cycle_days, ""


def bonus_salary_base(emp, cfg):
    basis = cfg["bonus_salary_basis"]
    if basis == "annual_basic":
        return emp["monthly_basic"] * 12
    if basis == "annual_fixed":
        return (emp["monthly_basic"] + emp.get("monthly_fixed_allowances", 0)) * 12
    if basis == "approved_eligible":
        return emp["approved_eligible_salary"]
    if basis == "fixed_target_amount":
        return None
    raise ValueError(f"Unknown salary basis {basis}")


def calc_bonus(emp, rating, cpf, cfg):
    """Annual Bonus = Eligible Salary x Target % x CPF x Individual Multiplier x Proration."""
    out = {"employee_id": emp["employee_id"], "flags": []}
    if not emp.get("bonus_eligible", True):
        out.update(bonus=0.0, reason="NOT_BONUS_ELIGIBLE")
        return out
    if emp.get("exit_type") in ("resignation", "termination"):
        out["flags"].append("LEAVER_RULE_REQUIRES_LEGAL_VALIDATION")
    proration, why = bonus_proration(emp, cfg)
    base = bonus_salary_base(emp, cfg)
    target_amount = emp["fixed_target_bonus"] if base is None else base * emp["target_bonus_pct"]
    mult = cfg["bonus_multipliers"][rating]
    bonus = target_amount * cpf * mult * proration
    out.update(salary_base=base, target_amount=target_amount, cpf=cpf, multiplier=mult,
               proration=round_half_up(proration, 4), bonus=round_half_up(bonus, 2),
               reason=why)
    return out


def bonus_budget_summary(results, budget):
    liability = round_half_up(sum(r["bonus"] for r in results), 2)
    target_total = round_half_up(sum(r.get("target_amount") or 0 for r in results), 2)
    funding_factor = 1.0 if budget is None or liability <= budget else budget / liability
    return {
        "calculated_liability": liability,
        "target_bonus_total": target_total,
        "budget": budget,
        "remaining_budget": None if budget is None else round_half_up(budget - liability, 2),
        "utilisation_pct": None if not budget else round_half_up(liability / budget * 100, 2),
        "funding_factor_if_approved": round_half_up(funding_factor, 4),
    }


# ---------------------------------------------------------------------------
# Merit
# ---------------------------------------------------------------------------

def compa_ratio(salary, midpoint):
    return round_half_up(salary / midpoint * 100, 2)


def cr_band(cr, cfg):
    for lower, key in cfg["cr_bands"]:
        if cr >= lower:
            return key
    raise AssertionError("unreachable")


def calc_merit(emp, rating, cfg, budget_scale=1.0):
    """Merit = matrix % (rating x compa-ratio band) x optional approved budget scale."""
    out = {"employee_id": emp["employee_id"], "flags": []}
    salary = emp["monthly_basic"]
    cr = compa_ratio(salary, emp["range_mid"])
    band = cr_band(cr, cfg)
    out.update(current_salary=salary, compa_ratio=cr, cr_band=band)

    if not emp.get("merit_eligible", True):
        out.update(merit_pct=0.0, increase=0.0, new_salary=salary, new_compa_ratio=cr,
                   status="NOT_ELIGIBLE")
        return out
    if _d(emp["employment_date"]) >= _d(cfg["merit_eligibility_cutoff"]):
        out.update(merit_pct=0.0, increase=0.0, new_salary=salary, new_compa_ratio=cr,
                   status="JOINED_AFTER_CUTOFF")
        return out
    if emp.get("exit_date"):
        out.update(merit_pct=0.0, increase=0.0, new_salary=salary, new_compa_ratio=cr,
                   status="LEAVER")
        return out

    pct = cfg["merit_matrix"][rating][band] * budget_scale
    pct = min(max(pct, cfg["merit_min_pct"]), cfg["merit_max_pct"])
    increase = round_half_up(salary * pct, 2)
    new_salary = round_half_up(salary + increase, 2)
    status = "PROPOSED"
    if salary >= emp["range_max"]:
        status = "REVIEW_AT_OR_ABOVE_RANGE_MAX"
        out["flags"].append("CURRENT_SALARY_AT_OR_ABOVE_MAX")
    elif new_salary > emp["range_max"]:
        status = "REVIEW_EXCEEDS_RANGE_MAX"
        out["flags"].append(f"EXCEEDS_MAX_BY_{round_half_up(new_salary - emp['range_max'], 2)}")
    if salary < emp["range_min"]:
        out["flags"].append("BELOW_RANGE_MIN_CONSIDER_EQUITY_ADJUSTMENT")
    out.update(merit_pct=round_half_up(pct, 5), increase=increase, new_salary=new_salary,
               new_compa_ratio=compa_ratio(new_salary, emp["range_mid"]), status=status)
    return out


def merit_budget_fit(emps_with_ratings, cfg, budget_pct):
    """Matrix cost vs a budget and the uniform scale that would make the matrix fit it.

    Returns cost in monthly payroll terms (annual cost = x12). The scale factor is
    a decision aid: applying it is an executive decision, recorded in the audit log.
    """
    eligible_payroll = 0.0
    matrix_cost = 0.0
    for emp, rating in emps_with_ratings:
        r = calc_merit(emp, rating, cfg)
        if r["status"] in ("NOT_ELIGIBLE", "JOINED_AFTER_CUTOFF", "LEAVER"):
            continue
        eligible_payroll += emp["monthly_basic"]
        matrix_cost += r["increase"]
    budget = eligible_payroll * budget_pct
    return {
        "budget_pct": budget_pct,
        "eligible_monthly_payroll": round_half_up(eligible_payroll, 2),
        "budget_monthly": round_half_up(budget, 2),
        "matrix_cost_monthly": round_half_up(matrix_cost, 2),
        "matrix_cost_pct_of_payroll": round_half_up(matrix_cost / eligible_payroll * 100, 3) if eligible_payroll else 0,
        "variance_monthly": round_half_up(budget - matrix_cost, 2),
        "scale_to_fit": round_half_up(budget / matrix_cost, 4) if matrix_cost else None,
    }
