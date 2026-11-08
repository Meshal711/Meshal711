# Enerco PMS Calculation Engine (reference implementation)

Phase 1 Python implementation of every formula in the system. The future FastAPI service will import this package directly, and the Excel workbook will be reconciled against it.

| Module | Purpose |
|---|---|
| `enerco_pms/config.py` | All configurable parameters (weights, bands, curves, multipliers, matrices, budgets) and a configuration validator |
| `enerco_pms/scoring.py` | KPI curves (higher/lower/binary/milestone), anti-inflation controls, component scores, preliminary score, rating |
| `enerco_pms/distribution.py` | Guided-distribution analytics with binomial expected ranges and group-size rules (never changes ratings) |
| `enerco_pms/rewards.py` | Company factor (step/linear), bonus with eligibility and proration, compa-ratio, merit matrix with range-max review, budget fit |
| `enerco_pms/pipeline.py` | End-to-end cycle run, including calibration overrides |
| `enerco_pms/synthetic.py` | 120 deterministic synthetic employees with edge cases (no real data) |

## Run

```bash
pip install pytest
python -m pytest -v               # 69 tests
python run_phase1_validation.py   # writes 19_Testing/Phase1_Methodology_Validation_Report.md and CSVs
```

Requires Python 3.10+ and the standard library only (pytest for the tests).
