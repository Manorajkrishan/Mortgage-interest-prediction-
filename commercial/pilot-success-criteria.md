# Synthetic-data proof-of-concept (PoC) plan

## Scope
A controlled demo of repayments, five single-mortgage hypothetical rate scenarios, historical rate market context and an anonymous portfolio sensitivity endpoint. No production financial datasets, no identifying customer details, no recommendations, no loan approvals, and no lender-specific offered rates.

## Proposed evidence and acceptance gates (not achieved claims)
1. Arithmetic: independently reconcile capital-and-interest payment formula against trusted spreadsheet/reference for zero rate, low/high rates, 5-to-40-year terms, deposits, and rounding conventions.
2. Negative testing: reject invalid ranges, empty/oversized portfolios, unexpected PII fields and malformed requests; compare within 1p where relevant after agreeing precision policy.
3. Time-series: split by date, compare against naive baseline; do not claim future horizon accuracy until 3/6/12-month retrospective tests and uncertainty calibration are complete.
4. Regulatory: specialist review confirms whether each proposed workflow falls within FCA mortgage advice/arranging/financial promotion perimeter. Consumer paths remain educational until resolved.
5. Security: private access-controlled staging, no public unsecured API, network/TLS controls, production secrets managed, SCA/SAST, threat modelling, penetration test, rate limiting and audit logging, no PII in logs.
6. Data: documentary provenance, attribution and commercial rights for each source; remove/re-license the legacy CSV if provenance cannot be established.
7. Usability: recruit consented professionals, measure completion time and incorrect interpretations relative to a baseline, capture negative feedback.
8. Operational readiness: service-owner identified, error monitoring, change approvals, retention controls, recovery, support process and commercial/legal sign-off.

## Example synthetic pilot set
- Case A: £300k price, £60k deposit, 4.75% annual, 25 years
- Case B: £450k price, £90k deposit, 5.25% annual, 30 years
- Case C: £225k price, £45k deposit, 4.25% annual, 20 years
Evaluate 0 and ± rate-shock scenarios. Figures are hypothetical and no customer data is needed.

## Completion decision
Do not label a product as bank-ready simply because CI passes. A bank-grade decision requires recorded evidence from the purchaser's security, governance and product stakeholders.
