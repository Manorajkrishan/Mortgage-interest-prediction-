# Mortgage Intelligence — UK mortgage planning beta

**[Mortgage Intelligence V2](v2/README.md)** is the active rebuild of this repository. It provides a UK mortgage repayment calculator, illustrative rate-sensitivity scenarios and an experimental Bank of England Bank Rate outlook.

> **Research beta:** Not financial advice, not a live mortgage offer and not ready to sell as production SaaS. The dated historical rate snapshot is verified only through August 2026. Users must check current information and obtain qualified advice for individual mortgage decisions.

## Project layout

- `testir/`: React planning dashboard and scenario CSV export.
- `v2/api/app.py`: FastAPI endpoints for mortgage calculations, historical Bank Rate and experimental forecasts.
- `v2/api/tests/`: automated input, calculation and modelling checks.
- `v2/README.md`: setup, methodology, deployment and commercial-readiness requirements.
- `uk.csv`: legacy dataset through October 2023; its Bank_Rate column is used without dropping records for unrelated missing values.
- `look.py`, `testjr.ipynb`: **legacy prototype** preserved for reference; not the supported beta API.

Read the [V2 implementation guide](v2/README.md) before running or deploying. See the [GitHub Actions workflow](.github/workflows/mortgage-v2-ci.yml) for automated checks.
