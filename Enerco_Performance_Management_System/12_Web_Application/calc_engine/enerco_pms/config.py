"""Configurable parameters for the Enerco Performance & Total Rewards engine.

Every value here is a parameter, not a formula. HR changes these values
(through the System Configuration sheet / admin screen) without touching the
calculation code. Values marked PROPOSED are assumptions awaiting Enerco
approval; see 01_Strategy/Assumptions_Register.md.
"""

from copy import deepcopy

# ---------------------------------------------------------------------------
# Rating bands. Lower bounds are inclusive, upper bounds exclusive, evaluated
# on the score AFTER rounding to 2 decimals (half-up). This closes the
# 109.99 -> 110 style gaps in the approved table.
# ---------------------------------------------------------------------------

# Approved table (Master Prompt section 6).
BANDS_APPROVED = [
    # (rating, label, lower_bound_inclusive)
    (5, "Exceptional", 110.0),
    (4, "Exceeds Expectations", 100.0),
    (3, "Meets Expectations", 85.0),
    (2, "Partially Meets Expectations", 70.0),
    (1, "Does Not Meet Expectations", float("-inf")),
]

# Option A (PROPOSED for decision D-07): recentred so that 100 = full target
# achievement sits inside "Meets Expectations".
BANDS_OPTION_A = [
    (5, "Exceptional", 115.0),
    (4, "Exceeds Expectations", 105.0),
    (3, "Meets Expectations", 90.0),
    (2, "Partially Meets Expectations", 75.0),
    (1, "Does Not Meet Expectations", float("-inf")),
]

DEFAULT_CONFIG = {
    "entity": "ENERCO",
    "cycle_year": 2026,
    "cycle_start": "2026-01-01",
    "cycle_end": "2026-12-31",

    # --- Scoring -----------------------------------------------------------
    "score_scale_max": 120.0,             # all component scores use 0..120
    "weights_default": {"kpi": 0.70, "competency": 0.20, "behavior": 0.10},
    # Approved job-family overrides (must each sum to 1.0). Empty = none approved yet.
    "weights_by_job_family": {},
    "rating_bands": BANDS_APPROVED,
    "score_rounding_dp": 2,

    # KPI scoring curve: score at threshold / target / stretch points.
    "kpi_curve_scores": {"floor": 0.0, "threshold": 70.0, "target": 100.0, "stretch": 120.0},
    # Controls against inflated KPI scores (PROPOSED).
    "kpi_cap_without_evidence": 100.0,     # no verified evidence -> cannot exceed target
    "kpi_cap_unapproved_stretch": 100.0,   # stretch above target needs HR-approved stretch value
    "kpi_cap_binary": 100.0,
    "kpi_min_weight": 0.05,                # each KPI >= 5% of KPI component
    "kpi_max_weight": 0.40,                # each KPI <= 40%
    "kpi_min_count": 3,
    "kpi_max_count": 8,

    # Competency proficiency level -> score on the 0..120 scale (PROPOSED).
    "proficiency_scores": {1: 60.0, 2: 80.0, 3: 100.0, 4: 110.0, 5: 120.0},

    # --- Guided distribution -----------------------------------------------
    "guided_distribution": {5: 0.05, 4: 0.15, 3: 0.60, 2: 0.15, 1: 0.05},
    "dist_min_group_size_full": 20,        # full statistical comparison
    "dist_min_group_size_indicative": 10,  # indicative only, warn
    "dist_alert_confidence": 0.90,         # binomial interval used to flag variance

    # --- Bonus --------------------------------------------------------------
    "bonus_salary_basis": "annual_basic",  # annual_basic | annual_fixed | approved_eligible | fixed_target_amount
    "bonus_target_pct_by_grade": {},       # filled from Job Grades table
    "bonus_multipliers": {5: 1.50, 4: 1.25, 3: 1.00, 2: 0.50, 1: 0.00},
    "company_scorecard_weights": {"financial": 0.50, "operational": 0.30, "strategic": 0.20},
    # Step table: (lower_bound_inclusive, factor)
    "company_payout_table": [(110.0, 1.20), (100.0, 1.00), (90.0, 0.90), (80.0, 0.75), (70.0, 0.50), (float("-inf"), 0.00)],
    "company_payout_method": "step",       # step | linear (interpolate between table points)
    "bonus_min_service_days": 90,          # PROPOSED - requires legal validation
    "bonus_budget": None,                  # SAR, set per cycle

    # --- Merit --------------------------------------------------------------
    # Compa-ratio bands: (lower_bound_inclusive_percent, band_key)
    "cr_bands": [(110.0, "110+"), (100.0, "100-109.99"), (90.0, "90-99.99"), (80.0, "80-89.99"), (float("-inf"), "<80")],
    "merit_matrix": {
        5: {"<80": 0.08, "80-89.99": 0.07, "90-99.99": 0.06, "100-109.99": 0.04, "110+": 0.02},
        4: {"<80": 0.06, "80-89.99": 0.05, "90-99.99": 0.04, "100-109.99": 0.03, "110+": 0.01},
        3: {"<80": 0.04, "80-89.99": 0.03, "90-99.99": 0.02, "100-109.99": 0.015, "110+": 0.00},
        2: {"<80": 0.0, "80-89.99": 0.0, "90-99.99": 0.0, "100-109.99": 0.0, "110+": 0.0},
        1: {"<80": 0.0, "80-89.99": 0.0, "90-99.99": 0.0, "100-109.99": 0.0, "110+": 0.0},
    },
    "merit_min_pct": 0.0,
    "merit_max_pct": 0.10,
    "merit_eligibility_cutoff": "2026-10-01",  # PROPOSED: joined on/after -> not eligible this cycle
    "merit_budget_pct": 0.03,                  # of eligible base payroll
}


def get_config(**overrides):
    cfg = deepcopy(DEFAULT_CONFIG)
    cfg.update(overrides)
    return cfg


def validate_config(cfg):
    """Return a list of configuration errors. Empty list = valid."""
    errors = []
    w = cfg["weights_default"]
    if abs(sum(w.values()) - 1.0) > 1e-9:
        errors.append(f"Default weights sum to {sum(w.values())}, expected 1.0")
    for fam, fw in cfg["weights_by_job_family"].items():
        if abs(sum(fw.values()) - 1.0) > 1e-9:
            errors.append(f"Weights for job family {fam} sum to {sum(fw.values())}")
    bounds = [b[2] for b in cfg["rating_bands"]]
    if bounds != sorted(bounds, reverse=True):
        errors.append("Rating band lower bounds must be strictly descending")
    if bounds[-1] != float("-inf"):
        errors.append("Lowest rating band must be open-ended (-inf) so every score maps to a rating")
    if abs(sum(cfg["guided_distribution"].values()) - 1.0) > 1e-9:
        errors.append("Guided distribution must sum to 100%")
    cw = cfg["company_scorecard_weights"]
    if abs(sum(cw.values()) - 1.0) > 1e-9:
        errors.append("Company scorecard weights must sum to 100%")
    ps = cfg["proficiency_scores"]
    if max(ps.values()) > cfg["score_scale_max"]:
        errors.append("A proficiency score exceeds the score scale maximum")
    for rating, row in cfg["merit_matrix"].items():
        for band, pct in row.items():
            if not (cfg["merit_min_pct"] <= pct <= cfg["merit_max_pct"]):
                errors.append(f"Merit matrix cell {rating}/{band}={pct} outside min/max")
    return errors
