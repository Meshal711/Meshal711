# Enerco Enterprise Performance Management & Total Rewards System

**Owner:** HR Department, Enerco · **Scope:** Enerco (version 1); designed to scale to GetWater and IPTC
**Current status:** Phase 1 (Research and Architecture) is complete and **submitted for review**. Later phases start after Phase 1 approval.
**Data:** synthetic data only. No real employee data has been used.

## Start here

| Read | File |
|---|---|
| 1. Executive summary, architecture and all methodologies | [`01_Strategy/Phase1_Design_Specification.md`](01_Strategy/Phase1_Design_Specification.md) |
| 2. The four questions that block the next phases | [`01_Strategy/Phase1_Review_Questions.md`](01_Strategy/Phase1_Review_Questions.md) |
| 3. Decisions (approved and proposed) | [`01_Strategy/Decision_Register.md`](01_Strategy/Decision_Register.md) |
| 4. Working assumptions and their owners | [`01_Strategy/Assumptions_Register.md`](01_Strategy/Assumptions_Register.md) |
| 4a. **Excel Ranking & Bell Curve Calculator** | [`10_Excel_Models/Enerco_Performance_Ranking_BellCurve_Calculator.xlsx`](10_Excel_Models/Enerco_Performance_Ranking_BellCurve_Calculator.xlsx) |
| 5. Test evidence on 120 synthetic employees | [`19_Testing/Phase1_Methodology_Validation_Report.md`](19_Testing/Phase1_Methodology_Validation_Report.md) |
| 6. Saudi legal points for Legal Counsel | [`16_Saudi_Compliance/Phase1_Saudi_Compliance_Review.md`](16_Saudi_Compliance/Phase1_Saudi_Compliance_Review.md) |
| 7. Sources and their verification status | [`02_Research/Research_Reference_Library.md`](02_Research/Research_Reference_Library.md) |

## Phase status

| Phase | Status |
|---|---|
| 1 Research and system architecture | **Complete, awaiting review** |
| 2 Performance framework | Not started |
| 3 KPI and competency library | Not started |
| 4 Rating and scoring engine | Engine logic built and tested; documents wait on decision D-07 |
| 5 Hybrid bell curve and calibration | Analytics logic built and tested; committee documents not started |
| 6 Annual bonus engine | Engine logic built and tested; policy waits on Legal |
| 7 Merit increase engine | Engine logic built and tested; matrix level waits on D-16 |
| 8 Excel development | **Performance Ranking & Bell Curve Calculator delivered** (`10_Excel_Models`), verified: 0 mismatches over 1,440 + 7,560 scenario comparisons |
| 9 Power BI | Not started |
| 10 Web application | Calculation core only (`12_Web_Application/calc_engine`) |
| 11 Policy and governance | Not started |
| 12 Testing and QA | 69 automated engine tests passing |
| 13 Pilot | Not started |
| 14 Executive presentation | Not started |

## Directory

```
01_Strategy/            Phase 1 spec, decision & assumption registers, review questions
02_Research/            Research reference library
03_..18_                Later-phase folders (each README states its status)
12_Web_Application/     calc_engine/ – tested Python calculation engine
16_Saudi_Compliance/    Phase 1 compliance review (for Legal)
19_Testing/             Validation report, automated test run, CSV outputs
20_Executive_Presentation/
```
