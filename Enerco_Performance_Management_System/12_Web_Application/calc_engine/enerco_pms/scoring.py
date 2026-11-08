"""Performance scoring: KPI achievement, component scores, preliminary score, rating.

All component scores share one scale: 0..120, where 100 = fully achieved target /
fully proficient. This makes the 70/20/10 weighting mathematically consistent.
"""

from decimal import Decimal, ROUND_HALF_UP

HIGHER = "higher_is_better"
LOWER = "lower_is_better"
BINARY = "binary"
MILESTONE = "milestone"  # actual = fraction of milestones delivered on time (0..1)


def round_half_up(value, dp=2):
    q = Decimal(1).scaleb(-dp)
    return float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))


def _interpolate(x, points):
    """Piecewise-linear interpolation over ascending (x, y) points, clamped at both ends."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def validate_kpi(kpi):
    """Return a list of design errors (blocking) for a KPI definition."""
    errs = []
    mt = kpi["measure_type"]
    if mt == BINARY:
        return errs
    th, tg = kpi["threshold"], kpi["target"]
    st = kpi.get("stretch")
    if mt in (HIGHER, MILESTONE):
        if not th < tg:
            errs.append("threshold must be below target for a higher-is-better KPI")
        if st is not None and not st > tg:
            errs.append("stretch must be above target")
    elif mt == LOWER:
        if not th > tg:
            errs.append("threshold must be above target for a lower-is-better KPI")
        if st is not None and not st < tg:
            errs.append("stretch must be below target")
    else:
        errs.append(f"unknown measure_type {mt}")
    return errs


def kpi_flags(kpi):
    """Non-blocking quality flags that HR QA must review (target difficulty, data quality, changes)."""
    flags = []
    base = kpi.get("baseline")
    mt = kpi["measure_type"]
    if base is not None and mt in (HIGHER, MILESTONE) and kpi["target"] <= base:
        flags.append("TARGET_NOT_ABOVE_BASELINE")
    if base is not None and mt == LOWER and kpi["target"] >= base:
        flags.append("TARGET_NOT_BELOW_BASELINE")
    if not kpi.get("evidence_verified", False):
        flags.append("EVIDENCE_NOT_VERIFIED")
    if kpi.get("data_quality") == "unreliable":
        flags.append("DATA_QUALITY_UNRELIABLE")
    if kpi.get("target_changed") and not kpi.get("target_change_approved"):
        flags.append("UNAPPROVED_TARGET_CHANGE")
    return flags


def kpi_score(kpi, cfg):
    """Score one KPI on 0..120. Returns (score, applied_caps)."""
    errs = validate_kpi(kpi)
    if errs:
        raise ValueError(f"KPI {kpi.get('kpi_id')}: {'; '.join(errs)}")
    curve = cfg["kpi_curve_scores"]
    mt = kpi["measure_type"]
    actual = kpi["actual"]
    caps = []

    if mt == BINARY:
        raw = 100.0 if actual else 0.0
        ceiling = cfg["kpi_cap_binary"]
    else:
        th, tg = kpi["threshold"], kpi["target"]
        stretch_approved = kpi.get("stretch") is not None and kpi.get("stretch_approved", False)
        st = kpi["stretch"] if kpi.get("stretch") is not None else tg + (tg - th)
        floor = kpi.get("floor", th - (tg - th))
        sign = -1 if mt == LOWER else 1   # mirror lower-is-better onto an ascending axis
        pts = [(sign * floor, curve["floor"]), (sign * th, curve["threshold"]),
               (sign * tg, curve["target"]), (sign * st, curve["stretch"])]
        raw = _interpolate(sign * actual, pts)
        ceiling = cfg["score_scale_max"] if stretch_approved else cfg["kpi_cap_unapproved_stretch"]
        if not stretch_approved and raw > ceiling:
            caps.append("CAPPED_NO_APPROVED_STRETCH")

    flags = kpi_flags(kpi)
    if ("EVIDENCE_NOT_VERIFIED" in flags or "DATA_QUALITY_UNRELIABLE" in flags
            or "UNAPPROVED_TARGET_CHANGE" in flags):
        if raw > cfg["kpi_cap_without_evidence"]:
            caps.append("CAPPED_EVIDENCE_OR_DATA_QUALITY")
        ceiling = min(ceiling, cfg["kpi_cap_without_evidence"])
    score = max(0.0, min(raw, ceiling, cfg["score_scale_max"]))
    return score, caps


def kpi_component(kpis, cfg):
    total_w = sum(k["weight"] for k in kpis)
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"KPI weights sum to {total_w}, expected 1.0")
    return sum(k["weight"] * kpi_score(k, cfg)[0] for k in kpis)


def proficiency_component(levels, cfg, weights=None):
    """Average (or weighted average) of proficiency levels mapped to the 0..120 scale."""
    if not levels:
        raise ValueError("No competency/behavior assessments supplied")
    mapped = [cfg["proficiency_scores"][int(l)] for l in levels]
    if weights is None:
        return sum(mapped) / len(mapped)
    return sum(w * m for w, m in zip(weights, mapped)) / sum(weights)


def weights_for(job_family, cfg):
    return cfg["weights_by_job_family"].get(job_family, cfg["weights_default"])


def preliminary_score(kpi_score_value, competency_score, behavior_score, job_family, cfg):
    w = weights_for(job_family, cfg)
    raw = (kpi_score_value * w["kpi"] + competency_score * w["competency"]
           + behavior_score * w["behavior"])
    return round_half_up(raw, cfg["score_rounding_dp"])


def rating_for(score, cfg):
    """Map a (rounded) score to (rating, label). Half-open bands, no gaps."""
    s = round_half_up(score, cfg["score_rounding_dp"])
    for rating, label, lower in cfg["rating_bands"]:
        if s >= lower:
            return rating, label
    raise AssertionError("unreachable: lowest band is open-ended")
