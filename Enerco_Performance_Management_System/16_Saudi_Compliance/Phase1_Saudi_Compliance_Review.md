# Phase 1 Saudi Compliance Review

| Document control | |
|---|---|
| Document | Phase 1 Saudi Compliance Review |
| Version | 0.1 (draft for legal review) |
| Owner | HR Department, Enerco |
| Prepared | November 2026 |
| Approval authority | Legal Counsel, then HR Director |
| Status | **Not legal advice. Every item requires review by Enerco legal counsel before policy implementation.** |
| Next review | Before Phase 11 (Policy and Governance) |

## 1. Purpose and method

This review lists the Saudi legal and regulatory points that affect the design of the Performance Management and Total Rewards system. It separates **mandatory legal requirements** from **internal policy choices**.

**Research limitation (important):** in this working environment, the official government sites (hrsd.gov.sa, laws.boe.gov.sa, hrdf.org.sa) could not be opened directly. Web search returned official page titles and law-firm summaries but not the full official text. So:

- Where an article number and its content are given below, the status column shows whether it was **confirmed from a retrieved source in this session** or is **to be verified against the official Arabic text**.
- No provision is quoted verbatim unless it was retrieved. Paraphrases are marked as such.
- The Arabic text published by the Bureau of Experts at the Council of Ministers (laws.boe.gov.sa) prevails over any English translation.

## 2. Primary instruments

| Instrument | Reference | Status of reference |
|---|---|---|
| Saudi Labor Law (نظام العمل) | Royal Decree No. M/51 dated 23/08/1426H, as amended. The latest broad amendments were made by Royal Decree No. M/44 dated 08/02/1446H. | Amendment decree number and date confirmed by search results (nezams.com; HRSD news). |
| Labor Law amendments, effective date | HRSD announced that the amendments take effect from 19 February 2025. ILO NATLEX lists a different date (25 February 2025). | Found via search (HRSD news page title; NATLEX). The date difference must be checked by legal. |
| Implementing Regulations of the Labor Law | Ministerial resolution, as amended | To be verified |
| Personal Data Protection Law (PDPL, نظام حماية البيانات الشخصية) | Royal Decree No. M/19 dated 09/02/1443H, amended by Royal Decree No. M/148 dated 05/09/1444H | To be verified against official text |
| PDPL Implementing Regulations and the Regulations on Personal Data Transfer outside the Kingdom | Issued by SDAIA in September 2023 | Confirmed by law-firm summaries found via search (Clyde & Co, Sept 2023) |
| Proposed amendments to the PDPL Implementing Regulations | SDAIA public consultation opened 6 October 2026 and closed 5 November 2026 | Found via search (Al Tamimi, Akin Gump). **These are proposals and are not yet in force.** |

## 3. Findings by topic

### 3.1 Wage definitions and the legal status of the annual bonus — HIGH PRIORITY

| Item | Detail |
|---|---|
| Provision | Labor Law, **Article 2** (Definitions): *Basic Wage* and *Actual Wage*. |
| Content (paraphrase, to be verified) | The actual wage is the basic wage plus increments paid for the worker's effort or work risks, or due under the contract or work regulations. A **grant or bonus** counts as part of the actual wage where it is (a) stipulated in the employment contract, (b) stipulated in the work regulations, or (c) customarily granted so that workers regard it as part of their wage rather than a donation. Article 2 also states that, where the Law says "wage" without qualification, it means the actual wage. |
| Source status | Secondary sources found in search (Qoyod glossary) confirm the three alternative conditions and that M/44 did not change these definitions. The exact wording is **to be verified** against the official text. |
| Why it matters | Whether the bonus is legally part of the "actual wage" may affect wage-based entitlements such as end-of-service award calculations and leave pay. It may also affect whether a bonus can be withheld from leavers, or set to zero for low ratings or a weak company year. |
| Type | **Mandatory law.** How the bonus policy is worded and how it is applied over time (custom) are **internal choices with legal consequences**. |
| Design response | (1) The bonus engine supports a contractual "not eligible" status and flags every leaver case `LEAVER_RULE_REQUIRES_LEGAL_VALIDATION`. (2) Bonus policy wording (discretionary vs. guaranteed language, payment conditions) is reserved for legal counsel. (3) The audit trail records each year's payout decisions, which matters if "custom" is ever argued. |
| Required action | Legal counsel to advise on the policy wording, the leaver rules and the treatment of contracts that already mention bonuses. |

### 3.2 Changes to salary and contract terms

| Item | Detail |
|---|---|
| Provision | The Labor Law restricts changes to the employment contract and wage without the worker's written agreement. **The exact article number is to be confirmed by legal counsel.** |
| Implication | A merit increase is a favorable change and is not expected to raise a consent issue. Changes that **reduce** an existing contractual entitlement do raise one, for example removing a contractual bonus or moving to a lower salary basis. |
| Type | Mandatory law |
| Design response | The bonus salary basis is configurable per employee group. The system never lowers salary; merit only adds. Contractual bonus terms are captured per employee (`bonus_eligible`, contract type). |

### 3.3 Internal work regulations (لائحة تنظيم العمل)

| Item | Detail |
|---|---|
| Provision | The Labor Law requires employers above a size threshold to have work regulations based on the Ministry's model, approved by the Ministry. **Article numbers and threshold to be verified.** |
| Implication | If PMS consequences, such as PIP outcomes, warnings or bonus forfeiture, are written into the work regulations, Ministry requirements apply. If performance outcomes are kept separate from disciplinary penalties, the policy must say so. |
| Type | Mandatory requirement (to be confirmed). Placing PMS rules inside or outside the work regulations is a policy choice. |
| Required action | Legal counsel to confirm Enerco's approved work regulations and whether the new policies need to be filed. |

### 3.4 Equal treatment and non-discrimination

| Item | Detail |
|---|---|
| Provision | The 2024/2025 amendments are reported to strengthen equal treatment provisions (Rödl & Partner summary found in search). **The article and wording are to be verified.** |
| Implication | Calibration and pay decisions must be explainable by performance, role and pay position, not by nationality, gender, age or disability. |
| Design response | Nationality group is stored for statutory reporting only. It is **excluded** from the comparison-group rules and calibration screens. Phase 9 Power BI adds a pay-equity check (merit % and compa-ratio by group) visible only to HR and Legal. |
| Type | Mandatory law (to be verified). The equity analytics are an internal control. |

### 3.5 Poor performance and termination

| Item | Detail |
|---|---|
| Implication | A low rating or a PIP must **not** be presented as an automatic ground for dismissal. Termination grounds and notice and compensation rules sit in the Labor Law; the article mapping is to be confirmed by legal counsel. |
| Design response | The PIP template (Phase 11) will end in "review outcome" options decided with HR and Legal, not an automatic action. |
| Type | Mandatory law; the PIP process is an internal policy |

### 3.6 Wage payment, social insurance and reporting

| Item | Detail |
|---|---|
| Implication | Salary increases and bonus payments must flow through payroll and the Wage Protection System. Changes to contributory wage elements must be reflected in social insurance (GOSI) records. **Which wage elements are contributory, and the reporting timelines, are to be verified with Payroll and Legal.** |
| Design response | The merit output file includes effective date, old and new basic salary, and a "payroll/GOSI update required" indicator for Phase 8/10 integration. |
| Type | Mandatory (to be verified) |

### 3.7 Personal data protection (PDPL) — HIGH PRIORITY

| Requirement area | Summary | Source status | System design response |
|---|---|---|---|
| Lawful basis and notice | Employee data must be processed on a lawful basis with a privacy notice. Where legitimate interest is relied on, the Implementing Regulations require a documented assessment. | Law-firm summaries (Al Tamimi employer note; Clyde & Co) | Phase 11 delivers an employee privacy notice for the PMS and a processing assessment template. |
| Data subject rights | Access, correction, destruction, and the right to be informed. Controllers respond within 30 days, extendable in certain cases. | Law-firm summaries; to verify | Employee self-service shows the employee's own objectives, ratings, bonus and merit outcome. Correction requests are routed to HR and logged. |
| Data minimisation and retention | Keep only what is needed and no longer than necessary. The PDPL sets no fixed period. | Law-firm summaries | Analytical datasets use Employee ID, not names. A retention schedule is proposed (A-20) for legal approval. |
| Security and breach notification | Appropriate security measures. Notify SDAIA of qualifying breaches within 72 hours (current rule). | Law-firm summaries | Role-based access, encryption, audit log, and an incident runbook in Phase 10. |
| Cross-border transfer | Transfers outside the Kingdom are restricted under the Transfer Regulations. The 2026 proposals would expressly require storage in Saudi Arabia. | Search results (Akin Gump, Al Tamimi): proposals, not in force | **Design assumption:** host in the Kingdom (KSA cloud region or on-premises). This avoids rework if the proposals are adopted. |
| Sensitive data | Some categories carry stricter rules. Salary and performance data are confidential personal data regardless. | To verify | Salary and performance fields are visible only to authorised roles (see the RBAC matrix in the Design Specification). |

### 3.8 Cybersecurity

The National Cybersecurity Authority (NCA) publishes controls frameworks. Whether they bind Enerco depends on its sector and classification; energy-sector entities may fall in scope. **Applicability to be confirmed by Enerco IT/Information Security.** The Phase 10 web application is designed to common baseline controls regardless: SSO/MFA, least-privilege roles, audit logging, encryption in transit and at rest, and no public deployment.

### 3.9 Grievance and appeal

An internal appeal of performance ratings is an **internal policy choice**; no specific statutory performance-appeal procedure was identified. Employees keep their statutory rights to raise labor disputes. The appeal form and SLA (Phase 11) must state that the internal process does not limit those rights. **Legal to confirm the wording.**

## 4. Summary: mandatory law vs. internal policy

| Topic | Mandatory (subject to verification) | Internal policy choice |
|---|---|---|
| Bonus legal character | Article 2 wage definition | Policy wording, eligibility, leaver rules, payment timing |
| Salary changes | Consent for adverse contract or wage changes | Merit matrix, budget, effective date |
| Work regulations | Ministry-approved regulations | Whether PMS rules sit inside them |
| Equal treatment | Non-discrimination provisions | Pay equity analytics and calibration bias reviews |
| Termination | Labor Law termination provisions | PIP design |
| Data protection | PDPL and Implementing Regulations | Retention periods, access model, hosting choice |
| Appeals | — | Appeal process and SLA |

## 5. Actions for Legal Counsel (before Phase 11)

1. Confirm the Article 2 wording and advise on bonus policy language and leaver treatment.
2. Confirm the article governing adverse contract and wage changes, and whether any existing contracts state bonus terms.
3. Confirm the status of Enerco's work regulations and filing needs.
4. Confirm the equal treatment provisions in force after the M/44 amendments.
5. Approve the PDPL lawful basis, privacy notice, retention schedule and hosting location.
6. Confirm GOSI and WPS implications of merit and bonus payments with Payroll.
7. Monitor the outcome of SDAIA's October–November 2026 consultation.

## 6. Sources located in this session (search results; secondary unless stated)

- HRSD news: Labor Law amendments take effect — https://www.hrsd.gov.sa/en/media-center/news/وزارة-الموارد-البشرية-والتنمية-الاجتماعية-تعلن-عن-بدء-سريان-تعديلات-نظام-العمل (official; page title only retrieved)
- HRSD, Labor Law general provisions (definitions) — https://www.hrsd.gov.sa/التعريفات/الأحكام-العامة (official; full text not retrievable from this environment)
- ILO NATLEX entry for the amendment — https://natlex.ilo.org/dyn/natlex2/r/natlex/fe/details?p3_isn=117438
- Qoyod glossary, "Actual wage" — https://www.qoyod.com/en/glossary/actual-wage/
- Rödl & Partner, Saudi labor law 2025 amendments — https://www.roedl.com/insights/saudi-arabia-labor-law-amendments-impact
- Clyde & Co, KSA Labour Law amendments series — https://www.clydeco.com/en/insights/2025/03/ksa-labour-law-amendments-resignations
- Al Tamimi, PDPL key considerations for employers — https://www.tamimi.com/news/saudi-arabias-new-personal-data-protection-law-key-considerations-for-employers/
- Clyde & Co, PDPL Implementing Regulations — https://www.clydeco.com/en/insights/2023/09/saudi-arabia-issues-implementing-regulations
- Akin Gump, SDAIA proposed amendments — https://www.akingump.com/en/insights/alerts/saudi-data-and-ai-authority-proposes-amendments-to-implementing-regulations-of-the-pdpl-10-key-proposed-changes
- Al Tamimi, SDAIA public consultation (October 2026) — https://www.tamimi.com/news/sdaia-opens-public-consultation-on-proposed-amendments-to-the-pdpl-implementing-regulation/

**To complete the legal verification, these hosts need to be reachable from the work environment:** laws.boe.gov.sa, hrsd.gov.sa, sdaia.gov.sa. Alternatively, Legal can supply the official PDFs.
