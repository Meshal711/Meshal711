"""End-to-end pipeline: performance inputs -> scores -> ratings -> bonus -> merit."""

from .scoring import (kpi_component, kpi_flags, kpi_score, preliminary_score,
                      proficiency_component, rating_for)
from .rewards import calc_bonus, calc_merit


def score_employee(emp, cfg):
    kpi = kpi_component(emp["kpis"], cfg)
    comp = proficiency_component(emp["competency_levels"], cfg)
    beh = proficiency_component(emp["behavior_levels"], cfg)
    pre = preliminary_score(kpi, comp, beh, emp["job_family"], cfg)
    rating, label = rating_for(pre, cfg)
    flags = sorted({f for k in emp["kpis"] for f in kpi_flags(k)}
                   | {c for k in emp["kpis"] for c in kpi_score(k, cfg)[1]})
    return {"employee_id": emp["employee_id"], "kpi_score": kpi, "competency_score": comp,
            "behavior_score": beh, "preliminary_score": pre, "preliminary_rating": rating,
            "preliminary_label": label, "qa_flags": flags}


def run_cycle(emps, cfg, cpf, final_rating_overrides=None, merit_scale=1.0):
    """final_rating_overrides: {employee_id: rating} approved by the calibration committee."""
    overrides = final_rating_overrides or {}
    out = []
    for e in emps:
        s = score_employee(e, cfg)
        final = overrides.get(e["employee_id"], s["preliminary_rating"])
        s["final_rating"] = final
        s["calibrated"] = final != s["preliminary_rating"]
        s["bonus"] = calc_bonus(e, final, cpf, cfg)
        s["merit"] = calc_merit(e, final, cfg, merit_scale)
        out.append(s)
    return out
