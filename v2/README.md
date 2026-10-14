# Mortgage Intelligence — V2 research beta

A UK-focused **educational** mortgage calculator and *experimental* Bank of England Bank Rate modelling dashboard. This is not a mortgage rate comparison service, lender eligibility checker, credit decision engine or regulated mortgage advice system.

## What is implemented
- Capital-and-interest monthly repayments, borrowing amount, LTV and lifetime interest.
- Five +/- 0.5 / 1.0 percentage-point hypothetical rate scenarios and CSV export.
- Historical Bank Rate series with corrected day-first dates and without dropping complete rate rows because other financial columns are missing.
- Official BoE IADB **IUMBEDR** monthly-end Bank Rate updates through **August 2026** (last verified period, not presented as live).
- Walk-forward evaluation over 24 held-out monthly observations comparing a lagged Ridge regressor against the naive last-observation baseline. The Ridge model is selected only when its MAE improves the baseline by at least 10%; otherwise the baseline is used.
- Illustrative uncertainty bands, source metadata and explicit warnings about prediction limitations.
- Input constraints, restrictive origin allow-list, backend tests and frontend build CI.

## Run locally
From the repo root, with Python 3.11+:

\`\`\`bash
python -m venv .venv
# activate your virtualenv
pip install -r requirements.txt
uvicorn v2.api.app:app --reload --port 8000
pytest -q v2/api/tests
\`\`\`

In another terminal:

\`\`\`bash
cd testir
cp .env.example .env.local
npm ci
npm start
\`\`\`

Open http://localhost:3000. The API documentation is at http://localhost:8000/docs.

## Deployment
- Frontend: existing \`testir/\` Create React App; use \`npm ci && npm run build\` and publish the \`build/\` directory. Set \`REACT_APP_API_BASE_URL\` to the **HTTPS** API origin (no trailing slash). This variable is baked into the static build.
- Backend: use \`v2/api/Dockerfile\` with the **repository root as build context**, or run \`uvicorn v2.api.app:app --host 0.0.0.0 --port $PORT\`. Set \`ALLOWED_ORIGINS\` to the exact HTTPS frontend origin(s), comma-separated.
- Keep preview deployments access-controlled. Do not launch financial-facing production use before review of security, data licenses, user communications, accuracy and FCA regulatory perimeter.
- No database, auth, Stripe billing, tenant isolation, audit logs or payment service is provided in this beta. **Do not sell SaaS subscriptions as if these are implemented.**

## Model and data limits
- Legacy CSV: \`uk.csv\`, 1999–October 2023. Bank_Rate fractions are converted to percent. Missing values in *other* columns do not invalidate Bank_Rate.
- Official update: [Bank of England IADB IUMBEDR](https://www.bankofengland.co.uk/boeapps/database/), November 2023–August 2026. This is a **static verified snapshot**; before public release build an official-data refresh job, licensing review, and freshness checks.
- A Bank Rate forecast is **not** an actual offered mortgage interest rate. Future BoE decisions depend on inflation, markets and policy, not just historical rate lags.
- One-step-ahead walk-forward MAE does *not* validate the accuracy of 12-month recursive forecasts. Bands are illustrative rather than statistically calibrated.
- No user financial data is stored by this API or UI. Only input parameters are processed for a request; infrastructure/access logs may still record technical metadata.

## Commercial readiness checklist
- [ ] Confirm legacy dataset provenance and rights for commercial redistribution; replace if necessary.
- [ ] Current official BoE feed and stale-data monitoring.
- [ ] Security assessment, rate limiting, error monitoring, legal privacy/cookie terms, uptime and backups.
- [ ] Automated frontend interactions and end-to-end tests, accessibility review.
- [ ] Independent quantitative model audit with regime and horizon-specific backtesting.
- [ ] Identity, organisations, subscriptions/payments, billing webhooks and tenancy isolation.
- [ ] FCA/legal review before regulated mortgage introductions, product recommendations or lender integrations.
- [ ] User interviews and willingness-to-pay validation before setting prices.

### Source and regulatory references
- [Bank of England IADB](https://www.bankofengland.co.uk/boeapps/database/)
- [FCA mortgage brokers](https://www.fca.org.uk/firms/authorisation/mortgage-brokers)
- [FCA advice vs information](https://handbook.fca.org.uk/handbook/perg4/perg4s6)
- [FCA financial promotions](https://www.fca.org.uk/firms/financial-promotions-adverts)
