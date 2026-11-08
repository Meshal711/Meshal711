"""Independent checks of the reference engine. Expected values are hand-calculated."""

import pytest

from enerco_pms.config import BANDS_OPTION_A, get_config, validate_config
from enerco_pms.distribution import analyse_group, binomial_interval
from enerco_pms.pipeline import run_cycle
from enerco_pms.rewards import (calc_bonus, calc_merit, company_factor, company_score,
                                compa_ratio, cr_band, merit_budget_fit)
from enerco_pms.scoring import (kpi_component, kpi_score, preliminary_score,
                                proficiency_component, rating_for, round_half_up)
from enerco_pms.synthetic import generate

CFG = get_config()


def kpi(**kw):
    base = {"kpi_id": "T", "weight": 1.0, "evidence_verified": True, "data_quality": "verified"}
    base.update(kw)
    return base


# ---------------------------------------------------------------- config
def test_default_config_valid():
    assert validate_config(CFG) == []


def test_config_rejects_bad_weights():
    assert validate_config(get_config(weights_default={"kpi": 0.7, "competency": 0.2, "behavior": 0.2}))


# ---------------------------------------------------------------- KPI curve
@pytest.mark.parametrize("actual,expected", [
    (85, 70.0),     # at threshold
    (100, 100.0),   # at target
    (115, 120.0),   # at approved stretch
    (130, 120.0),   # capped at scale max
    (92.5, 85.0),   # halfway threshold->target: 70 + 0.5*30
    (107.5, 110.0), # halfway target->stretch: 100 + 0.5*20
    (70, 0.0),      # floor = threshold - (target - threshold) = 70
    (77.5, 35.0),   # halfway floor->threshold
])
def test_higher_is_better_curve(actual, expected):
    k = kpi(measure_type="higher_is_better", threshold=85, target=100, stretch=115, stretch_approved=True, actual=actual)
    assert kpi_score(k, CFG)[0] == pytest.approx(expected)


@pytest.mark.parametrize("actual,expected", [(12, 70.0), (10, 100.0), (8.5, 120.0), (11, 85.0), (14, 0.0)])
def test_lower_is_better_curve(actual, expected):
    k = kpi(measure_type="lower_is_better", threshold=12, target=10, stretch=8.5, stretch_approved=True, actual=actual)
    assert kpi_score(k, CFG)[0] == pytest.approx(expected)


def test_no_approved_stretch_caps_at_100():
    k = kpi(measure_type="higher_is_better", threshold=85, target=100, actual=140)
    score, caps = kpi_score(k, CFG)
    assert score == 100.0 and "CAPPED_NO_APPROVED_STRETCH" in caps


def test_unverified_evidence_caps_at_100_even_with_stretch():
    k = kpi(measure_type="higher_is_better", threshold=85, target=100, stretch=115, stretch_approved=True,
            actual=115, evidence_verified=False)
    assert kpi_score(k, CFG)[0] == 100.0


def test_binary_kpi_cannot_exceed_target():
    assert kpi_score(kpi(measure_type="binary", actual=1), CFG)[0] == 100.0
    assert kpi_score(kpi(measure_type="binary", actual=0), CFG)[0] == 0.0


def test_milestone_kpi():
    k = kpi(measure_type="milestone", threshold=0.7, target=1.0, actual=0.85)
    assert kpi_score(k, CFG)[0] == pytest.approx(85.0)


def test_invalid_kpi_rejected():
    with pytest.raises(ValueError):
        kpi_score(kpi(measure_type="higher_is_better", threshold=100, target=90, actual=95), CFG)
    with pytest.raises(ValueError):
        kpi_score(kpi(measure_type="lower_is_better", threshold=8, target=10, actual=9), CFG)


def test_kpi_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        kpi_component([kpi(measure_type="binary", actual=1, weight=0.6)], CFG)


def test_kpi_component_weighted():
    ks = [kpi(measure_type="binary", actual=1, weight=0.5),
          kpi(measure_type="higher_is_better", threshold=85, target=100, actual=92.5, weight=0.5)]
    assert kpi_component(ks, CFG) == pytest.approx(0.5 * 100 + 0.5 * 85)


# ---------------------------------------------------------------- weighting & rating
def test_weighting_70_20_10():
    # 110*0.7 + 90*0.2 + 100*0.1 = 77 + 18 + 10 = 105
    assert preliminary_score(110, 90, 100, None, CFG) == 105.0


def test_proficiency_mapping():
    assert proficiency_component([3, 3, 4, 5, 2], CFG) == pytest.approx((100 + 100 + 110 + 120 + 80) / 5)


def test_job_family_override():
    cfg = get_config(weights_by_job_family={"Sales": {"kpi": 0.8, "competency": 0.15, "behavior": 0.05}})
    assert preliminary_score(100, 80, 60, "Sales", cfg) == 80 + 12 + 3


@pytest.mark.parametrize("score,rating", [
    (120, 5), (110, 5), (109.995, 5), (109.99, 4), (100, 4), (99.99, 3), (85, 3),
    (84.99, 2), (70, 2), (69.99, 1), (0, 1)])
def test_approved_band_boundaries(score, rating):
    assert rating_for(score, CFG)[0] == rating


def test_every_score_maps_to_exactly_one_rating():
    cfg_a = get_config(rating_bands=BANDS_OPTION_A)
    for i in range(0, 12001):
        s = i / 100
        for c in (CFG, cfg_a):
            assert rating_for(s, c)[0] in (1, 2, 3, 4, 5)


def test_rounding_half_up():
    assert round_half_up(99.995) == 100.0
    assert round_half_up(84.994) == 84.99


# ---------------------------------------------------------------- distribution
def test_binomial_interval_small_group_allows_zero():
    lo, hi = binomial_interval(10, 0.05, 0.90)
    assert lo == 0  # zero 'Exceptional' in a team of 10 is normal


def test_distribution_never_changes_ratings():
    ratings = [3] * 18 + [4, 5]
    before = list(ratings)
    analyse_group(ratings, CFG)
    assert ratings == before


def test_small_group_status():
    assert analyse_group([3, 3, 4], CFG)["status"] == "TOO_SMALL_QUALITATIVE_REVIEW"
    assert analyse_group([3] * 12, CFG)["status"] == "INDICATIVE_ONLY"
    assert analyse_group([3] * 25, CFG)["status"] == "FULL_COMPARISON"


# ---------------------------------------------------------------- company factor & bonus
def test_company_score_weighting():
    # 100*0.5 + 90*0.3 + 80*0.2 = 50 + 27 + 16 = 93
    assert company_score({"financial": 100, "operational": 90, "strategic": 80}, CFG) == 93.0


@pytest.mark.parametrize("score,factor", [(69.99, 0.0), (70, 0.5), (79.99, 0.5), (80, 0.75), (89.99, 0.75),
                                          (90, 0.9), (99.99, 0.9), (100, 1.0), (109.99, 1.0), (110, 1.2), (130, 1.2)])
def test_company_payout_step(score, factor):
    assert company_factor(score, CFG) == factor


def test_company_payout_linear():
    cfg = get_config(company_payout_method="linear")
    assert company_factor(75, cfg) == pytest.approx(0.625)
    assert company_factor(105, cfg) == pytest.approx(1.1)
    assert company_factor(60, cfg) == 0.0


def emp(**kw):
    e = {"employee_id": "X1", "monthly_basic": 10000, "monthly_fixed_allowances": 3500, "target_bonus_pct": 0.10,
         "employment_date": "2020-01-01", "bonus_eligible": True, "merit_eligible": True,
         "range_min": 8333.33, "range_mid": 10000, "range_max": 11666.67, "unpaid_leave_days": 0}
    e.update(kw)
    return e


def test_bonus_formula_full_year():
    # 120,000 x 10% x 0.9 x 1.25 x 1 = 13,500
    assert calc_bonus(emp(), 4, 0.9, CFG)["bonus"] == 13500.0


def test_bonus_excludes_allowances_by_default():
    assert calc_bonus(emp(), 3, 1.0, CFG)["salary_base"] == 120000


def test_bonus_annual_fixed_basis():
    cfg = get_config(bonus_salary_basis="annual_fixed")
    assert calc_bonus(emp(), 3, 1.0, cfg)["bonus"] == pytest.approx(162000 * 0.10)


def test_bonus_proration_new_joiner():
    # Joined 2026-07-01: 184 of 365 days. 120000*0.1*1*1*(184/365)
    r = calc_bonus(emp(employment_date="2026-07-01"), 3, 1.0, CFG)
    assert r["bonus"] == round_half_up(12000 * 184 / 365, 2)


def test_bonus_unpaid_leave_reduces_proration():
    r = calc_bonus(emp(unpaid_leave_days=73), 3, 1.0, CFG)
    assert r["bonus"] == round_half_up(12000 * 292 / 365, 2)


def test_bonus_min_service_and_ineligible():
    assert calc_bonus(emp(employment_date="2026-11-15"), 5, 1.0, CFG)["bonus"] == 0.0
    assert calc_bonus(emp(bonus_eligible=False), 5, 1.0, CFG)["bonus"] == 0.0


def test_bonus_leaver_flagged_for_legal():
    r = calc_bonus(emp(exit_date="2026-06-30", exit_type="resignation"), 3, 1.0, CFG)
    assert "LEAVER_RULE_REQUIRES_LEGAL_VALIDATION" in r["flags"]


def test_bonus_rating_1_pays_zero():
    assert calc_bonus(emp(), 1, 1.2, CFG)["bonus"] == 0.0


# ---------------------------------------------------------------- merit
def test_compa_ratio_and_band():
    assert compa_ratio(9500, 10000) == 95.0
    assert cr_band(95.0, CFG) == "90-99.99"
    assert cr_band(79.99, CFG) == "<80"
    assert cr_band(110.0, CFG) == "110+"


def test_merit_matrix_lookup():
    r = calc_merit(emp(monthly_basic=9500), 4, CFG)   # CR 95 -> 4% for Exceeds
    assert r["merit_pct"] == 0.04 and r["increase"] == 380.0 and r["new_salary"] == 9880.0
    assert r["new_compa_ratio"] == 98.8


def test_merit_exceeding_range_max_flagged_not_truncated():
    # CR 112 -> 110+ band, Exceptional 2%: 11200 -> 11424 (< max 11666.67)  ok
    # CR 114.5 with Exceptional 2%: 11450 -> 11679 > max -> review, amount NOT truncated
    r = calc_merit(emp(monthly_basic=11450), 5, CFG)
    assert r["status"] == "REVIEW_EXCEEDS_RANGE_MAX"
    assert r["new_salary"] == 11679.0


def test_merit_ineligible_cases():
    assert calc_merit(emp(merit_eligible=False), 5, CFG)["status"] == "NOT_ELIGIBLE"
    assert calc_merit(emp(employment_date="2026-10-15"), 5, CFG)["status"] == "JOINED_AFTER_CUTOFF"
    assert calc_merit(emp(exit_date="2026-05-01"), 5, CFG)["status"] == "LEAVER"


def test_merit_budget_fit_reconciles():
    pairs = [(emp(employee_id="A", monthly_basic=9500), 4), (emp(employee_id="B", monthly_basic=10500), 3)]
    m = merit_budget_fit(pairs, CFG, 0.03)
    # costs: 9500*4% = 380 ; 10500 CR105 -> 1.5% = 157.5 ; total 537.5
    assert m["matrix_cost_monthly"] == 537.5
    assert m["budget_monthly"] == 600.0
    assert m["scale_to_fit"] == round_half_up(600 / 537.5, 4)


# ---------------------------------------------------------------- end to end
def test_pipeline_runs_on_120_synthetic_employees():
    emps = generate(120)
    assert len(emps) == 120
    res = run_cycle(emps, get_config(rating_bands=BANDS_OPTION_A), 1.0)
    assert len(res) == 120
    for r in res:
        assert 0 <= r["preliminary_score"] <= 120
        assert r["final_rating"] == r["preliminary_rating"]
        assert r["bonus"]["bonus"] >= 0


def test_calibration_override_changes_only_target_and_follows_to_rewards():
    emps = generate(120)
    cfg = get_config(rating_bands=BANDS_OPTION_A)
    base = run_cycle(emps, cfg, 1.0)
    target = next(r for r in base if r["preliminary_rating"] == 3 and r["bonus"]["bonus"] > 0)
    cal = run_cycle(emps, cfg, 1.0, final_rating_overrides={target["employee_id"]: 4})
    changed = [r for r in cal if r["calibrated"]]
    assert [r["employee_id"] for r in changed] == [target["employee_id"]]
    after = changed[0]
    assert after["preliminary_rating"] == 3 and after["final_rating"] == 4
    assert after["bonus"]["bonus"] == pytest.approx(target["bonus"]["bonus"] * 1.25, abs=0.02)
