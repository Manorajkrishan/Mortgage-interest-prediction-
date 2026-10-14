# Data provenance, regulation and claims register

## Factual source checks as of 14 October 2026
- UK BoE policy rate: official September 2026 MPC decision maintained Bank Rate at 3.75%. https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/september-2026
- Historical aggregate quoted two-year mortgage rate for 95% LTV: IADB IUM2WTL reported 5.70% in September 2026. This is **not a lender offer**. https://www.bankofengland.co.uk/boeapps/database/
- Licence: Bank of England states its Database data is generally reused under UK Open Government Licence, but some series are excluded (such as selected exchange rates). Verify individual source conditions and attribution on each release. https://www.bankofengland.co.uk/legal
- Legacy CSV (1999–2023) included in original project has not undergone complete origin, revision and commercial re-use audit. Do not commercially redistribute it until verified.

## Product regulatory perimeter
The FCA mortgage advice perimeter can capture communications that go beyond neutral information and are objectively likely to influence specific mortgage decisions. The precise consumer journey matters, not merely labelling something 'educational'. See https://handbook.fca.org.uk/handbook/perg4 . Mortgage brokers conducting regulated activity generally need relevant authorisation or AR status; see https://www.fca.org.uk/firms/authorisation/mortgage-brokers.

Do not present the platform as FCA-registered, bank-approved, a lender or an eligible-mortgage recommendation service. Professional legal advice is required before live borrowers, paid regulated workflows, mortgage introductions or promotions.

## Claims we may make now
- The codebase contains a research beta implementing hypothetical repayment and rate-shock calculation.
- The React/API build and test workflow can be inspected in the PR's Actions.
- The BoE market index is a dated published aggregate with attribution.
- The forecast uses one-step-ahead historical evaluation, not proven future long-horizon skill.
- No current bank customers, paid subscriptions, production integrations, performance certifications or regulator permissions are established.

## Security blocker
The beta API is unauthenticated and has no deployed private staging access layer. Pydantic rejects unexpected customer-identifying JSON fields, but that is not a full data-protection control. Even synthetic demos must use HTTPS and verified access restrictions if deployed.

## Licence notices for displays
Bank of England IADB historical interest-rate data, copyright the Governor and Company of the Bank of England, reproduced under the Open Government Licence v3.0 where applicable. Mortgage index and policy rate are distinct. No Bank of England endorsement implied.
