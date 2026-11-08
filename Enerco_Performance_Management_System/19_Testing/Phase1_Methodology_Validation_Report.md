# Phase 1 Methodology Validation Report

**Data:** 120 synthetic Enerco employees (seed 2026). No real employee data was used.  
**Engine:** `12_Web_Application/calc_engine/enerco_pms` (Python reference implementation).  
**Status:** Generated automatically by `run_phase1_validation.py`. All figures below are outputs of the engine run, not estimates.

## 1. Rating scale alignment test

An employee who achieves every KPI target exactly (KPI score 100) and is rated fully proficient (level 3 = 100) on every competency and behavior:

| Band set | Preliminary score | Rating |
|---|---|---|
| Approved bands | 100.0 | Exceeds Expectations |
| Option A bands | 100.0 | Meets Expectations |

**Finding F-01:** under the approved bands, fully meeting every expectation produces **Exceeds Expectations**. See decision D-07 in the Phase 1 Design Specification.

### Boundary values (scores rounded half-up to 2 dp before banding)

| Raw score | Approved bands | Option A |
|---|---|---|
| 69.99 | Does Not Meet Expectations | Does Not Meet Expectations |
| 69.995 | Partially Meets Expectations | Does Not Meet Expectations |
| 70.0 | Partially Meets Expectations | Does Not Meet Expectations |
| 84.99 | Partially Meets Expectations | Partially Meets Expectations |
| 84.995 | Meets Expectations | Partially Meets Expectations |
| 85.0 | Meets Expectations | Partially Meets Expectations |
| 99.99 | Meets Expectations | Meets Expectations |
| 99.995 | Exceeds Expectations | Meets Expectations |
| 100.0 | Exceeds Expectations | Meets Expectations |
| 109.99 | Exceeds Expectations | Exceeds Expectations |
| 109.995 | Exceptional | Exceeds Expectations |
| 110.0 | Exceptional | Exceeds Expectations |
| 120.0 | Exceptional | Exceptional |

Every value maps to exactly one rating: there are no gaps (e.g. 109.995 is not lost between 109.99 and 110).

## 2. Preliminary rating distribution (no calibration applied)

| Band set | 5 Exceptional | 4 Exceeds | 3 Meets | 2 Partially | 1 Does not meet |
|---|---|---|---|---|---|
| Approved bands | 5 (4.2%) | 35 (29.2%) | 56 (46.7%) | 16 (13.3%) | 8 (6.7%) |
| Option A bands | 1 (0.8%) | 17 (14.2%) | 67 (55.8%) | 24 (20.0%) | 11 (9.2%) |
| Guideline | 5% | 15% | 60% | 15% | 5% |
| Option A, stretch cap off | 3 (2.5%) | 23 (19.2%) | 60 (50.0%) | 23 (19.2%) | 11 (9.2%) |

**Finding F-07:** when no HR-approved stretch value exists, the stretch control caps KPI scores at 100. That makes rating 5 rare, because an employee then needs mostly level-5 competencies to reach the band. Setting approved stretch values at objective-setting is therefore a required process step, not an option. The 'stretch cap off' row shows the effect of removing the control. It is not recommended, because it rewards targets that were set too low.

The synthetic population is generated around target performance. Under the approved bands, on-target performers shift into rating 4, which is Finding F-01 seen at population level.

## 3. Guided distribution analysis (Option A bands, company level)

Group size 120, status **FULL_COMPARISON**.

| Rating | Count | Actual | Guideline | Variance | Expected range (90%) | Flag |
|---|---|---|---|---|---|---|
| 5 | 1 | 0.8% | 5.0% | -4.2 pp | 2-10 | FLAG |
| 4 | 17 | 14.2% | 15.0% | -0.8 pp | 12-25 |  |
| 3 | 67 | 55.8% | 60.0% | -4.2 pp | 63-81 |  |
| 2 | 24 | 20.0% | 15.0% | +5.0 pp | 12-25 |  |
| 1 | 11 | 9.2% | 5.0% | +4.2 pp | 2-10 | FLAG |

### By department

| Department | n | Comparison status | Ratings outside range | P(no 'Exceptional' by chance) |
|---|---|---|---|---|
| Commercial | 13 | INDICATIVE_ONLY | - | 51.3% |
| Engineering | 31 | FULL_COMPARISON | - | 20.4% |
| Finance | 13 | INDICATIVE_ONLY | - | 51.3% |
| HSE | 5 | TOO_SMALL_QUALITATIVE_REVIEW | - | 77.4% |
| Human Resources | 6 | TOO_SMALL_QUALITATIVE_REVIEW | - | 73.5% |
| Operations | 26 | FULL_COMPARISON | - | 26.4% |
| Projects | 16 | INDICATIVE_ONLY | - | 44.0% |
| Supply Chain | 10 | INDICATIVE_ONLY | - | 59.9% |

**Finding F-02:** in a group of 20 with a 5% guideline, the chance of having nobody rated Exceptional is 35.8%. Small groups must not be forced to fill every category. The engine only flags a variance when the count falls outside the binomial range, and it never changes a rating.

## 4. Calibration override test

| Employee | Preliminary score | Preliminary rating | Final rating | Bonus before | Bonus after | Merit % before | Merit % after |
|---|---|---|---|---|---|---|---|
| EN1008 | 105.22 | 4 | 3 | 11,868 | 9,494 | 3.0% | 1.5% |

Only 1 record changed. The preliminary score is retained beside the final rating and rewards follow the final calibrated rating.

## 5. Annual bonus scenarios (Option A bands, illustrative target bonus % by grade)

| Scenario | Company score | CPF (step) | Target bonus pool (SAR) | Calculated liability (SAR) | Liability / target |
|---|---|---|---|---|---|
| Below threshold (company score 68) | 67.9 | 0.0 | 2,575,087 | 0 | 0.0% |
| On plan (company score 100) | 100.0 | 1.0 | 2,575,087 | 1,969,135 | 76.5% |
| Strong year (company score 112) | 112.1 | 1.2 | 2,575,087 | 2,362,962 | 91.8% |

Step vs. linear company payout factor (both supported by configuration):

| Company score | Step factor | Linear factor |
|---|---|---|
| 69.99 | 0.0 | 0.0 |
| 70 | 0.5 | 0.5 |
| 75 | 0.5 | 0.625 |
| 79.99 | 0.5 | 0.7497 |
| 80 | 0.75 | 0.75 |
| 95 | 0.9 | 0.95 |
| 105 | 1.0 | 1.1 |
| 110 | 1.2 | 1.2 |
| 115 | 1.2 | 1.2 |

**Finding F-03:** the step table creates cliffs. A company score of 79.99 pays 0.50 and 80.00 pays 0.75, a 50% jump in the bonus pool for 0.01 points. Linear interpolation is offered as an option for decision D-13.

**Finding F-04:** if final ratings matched the 5/15/60/15/5 guideline exactly, the average individual multiplier would be **0.9375**, so at CPF 1.00 the pool would be 93.75% of the target bonus pool. Finance can use this figure for accrual planning.

### Bonus eligibility edge cases

| Employee | Scenario | Proration | Bonus (SAR) | Reason | Flags |
|---|---|---|---|---|---|
| EN1003 | new_joiner_partial_year | 0.8 | 3,557 |  |  |
| EN1007 | new_joiner_after_cutoff | 0.0 | 0 | BELOW_MIN_SERVICE |  |
| EN1011 | joiner_below_min_service | 0.0 | 0 | BELOW_MIN_SERVICE |  |
| EN1015 | leaver_resignation | 0.6658 | 5,586 |  | LEAVER_RULE_REQUIRES_LEGAL_VALIDATION |
| EN1019 | leaver_termination | 0.4959 | 3,224 |  | LEAVER_RULE_REQUIRES_LEGAL_VALIDATION |
| EN1023 | unpaid_leave | 0.8767 | 10,952 |  |  |
| EN1027 | salary_above_range_max | 1.0 | 17,304 |  |  |
| EN1031 | salary_near_range_max | 1.0 | 16,716 |  |  |
| EN1035 | salary_below_range_min | 1.0 | 24,840 |  |  |
| EN1039 | contractually_not_bonus_eligible | - | 0 | NOT_BONUS_ELIGIBLE |  |
| EN1043 | not_merit_eligible | 1.0 | 12,504 |  |  |
| EN1047 | incomplete_evidence | 1.0 | 2,401 |  |  |
| EN1051 | unapproved_target_change | 1.0 | 0 |  |  |
| EN1055 | target_below_baseline | 1.0 | 13,284 |  |  |

## 6. Merit budget simulation (Option A ratings, illustrative matrix)

| Budget | Eligible monthly payroll | Annual budget (SAR) | Annual matrix cost (SAR) | Matrix cost % payroll | Annual variance (SAR) | Uniform scale to fit |
|---|---|---|---|---|---|---|
| 2.0% | 1,678,070 | 402,737 | 208,616 | 1.04% | 194,121 | 1.9305 |
| 3.0% | 1,678,070 | 604,105 | 208,616 | 1.04% | 395,489 | 2.8958 |
| 4.0% | 1,678,070 | 805,474 | 208,616 | 1.04% | 596,858 | 3.861 |

**Finding F-05:** the illustrative matrix has a fixed cost that depends on the rating mix and compa-ratio mix. It does not automatically equal any budget. The engine reports the uniform scale factor that would fit each budget. Applying it is an executive decision, and ratings are never changed.

**Finding F-06:** even if ratings followed the 5/15/60/15/5 guideline exactly, the illustrative matrix would cost about **1.43% of eligible payroll** with this compa-ratio mix. That is below a 2%, 3% or 4% budget, so the matrix percentages have to be calibrated to the approved budget before they can be used (decision D-16).

### Merit status counts

| Status | Employees |
|---|---|
| JOINED_AFTER_CUTOFF | 2 |
| LEAVER | 2 |
| NOT_ELIGIBLE | 1 |
| PROPOSED | 109 |
| REVIEW_AT_OR_ABOVE_RANGE_MAX | 6 |

### Merit exceptions requiring review

| Employee | Scenario | CR | CR band | Merit % | New CR | Status | Flags |
|---|---|---|---|---|---|---|---|
| EN1004 | standard | 117.25 | 110+ | 0.0% | 117.25 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1007 | new_joiner_after_cutoff | 101.95 | 100-109.99 | 0.0% | 101.95 | JOINED_AFTER_CUTOFF |  |
| EN1011 | joiner_below_min_service | 98.44 | 90-99.99 | 0.0% | 98.44 | JOINED_AFTER_CUTOFF |  |
| EN1015 | leaver_resignation | 89.18 | 80-89.99 | 0.0% | 89.18 | LEAVER |  |
| EN1017 | standard | 116.67 | 110+ | 0.0% | 116.67 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1019 | leaver_termination | 112.87 | 110+ | 0.0% | 112.87 | LEAVER |  |
| EN1025 | standard | 82.5 | 80-89.99 | 5.0% | 86.63 | PROPOSED | BELOW_RANGE_MIN_CONSIDER_EQUITY_ADJUSTMENT |
| EN1027 | salary_above_range_max | 120.17 | 110+ | 0.0% | 120.17 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1035 | salary_below_range_min | 76.67 | <80 | 0.0% | 76.67 | PROPOSED | BELOW_RANGE_MIN_CONSIDER_EQUITY_ADJUSTMENT |
| EN1043 | not_merit_eligible | 106.33 | 100-109.99 | 0.0% | 106.33 | NOT_ELIGIBLE |  |
| EN1091 | standard | 117.26 | 110+ | 0.0% | 117.26 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1094 | standard | 117.25 | 110+ | 0.0% | 117.25 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1106 | standard | 117.41 | 110+ | 0.0% | 117.41 | REVIEW_AT_OR_ABOVE_RANGE_MAX | CURRENT_SALARY_AT_OR_ABOVE_MAX |
| EN1107 | standard | 82.35 | 80-89.99 | 5.0% | 86.46 | PROPOSED | BELOW_RANGE_MIN_CONSIDER_EQUITY_ADJUSTMENT |
| EN1117 | standard | 82.58 | 80-89.99 | 3.0% | 85.06 | PROPOSED | BELOW_RANGE_MIN_CONSIDER_EQUITY_ADJUSTMENT |

Increases that would take salary above range maximum are **flagged for review, not truncated**.

### Annual merit cost by grade (matrix as illustrated)

| Grade | Annual cost (SAR) |
|---|---|
| G05 | 11,548 |
| G06 | 6,966 |
| G07 | 29,825 |
| G08 | 46,235 |
| G09 | 25,675 |
| G10 | 24,820 |
| G11 | 46,291 |
| G12 | 11,279 |
| G13 | 5,976 |

## 7. KPI quality-control flags raised

| Flag | KPIs/employees affected |
|---|---|
| CAPPED_NO_APPROVED_STRETCH | 64 |
| EVIDENCE_NOT_VERIFIED | 1 |
| TARGET_NOT_ABOVE_BASELINE | 1 |
| UNAPPROVED_TARGET_CHANGE | 1 |

KPI scores with unverified evidence, unreliable data or unapproved target changes are capped at 100. KPIs above target need an HR-approved stretch value to score above 100. Targets that are not harder than the baseline are flagged for HR QA.

