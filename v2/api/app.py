"""Mortgage Intelligence V2 - educational calculations and experimental UK rate outlook.

Run from repository root: uvicorn v2.api.app:app --reload --port 8000
No lender eligibility, credit decisions or regulated recommendations are provided.
"""
from __future__ import annotations

import base64
import binascii
import csv
import hmac
import math
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from statistics import mean

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, model_validator
from sklearn.linear_model import Ridge

VERSION = "2.0.0-beta"
DATA_FILE = Path(__file__).resolve().parents[2] / "uk.csv"

# Official BoE IADB series IUMBEDR, end-of-month Bank Rate (%).
# Monthly IADB historical data to August 2026 plus official September 2026 MPC decision.
# This is a dated research snapshot, not a live feed.
# https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/september-2026
# https://www.bankofengland.co.uk/boeapps/database/ (series IUMBEDR)
BOE_VERIFIED = {
    "2023-11": 5.25, "2023-12": 5.25,
    **{f"2024-{m:02d}": 5.25 for m in range(1, 8)},
    **{f"2024-{m:02d}": 5.00 for m in range(8, 11)},
    "2024-11": 4.75, "2024-12": 4.75,
    "2025-01": 4.75,
    **{f"2025-{m:02d}": 4.50 for m in range(2, 5)},
    **{f"2025-{m:02d}": 4.25 for m in range(5, 8)},
    **{f"2025-{m:02d}": 4.00 for m in range(8, 12)},
    "2025-12": 3.75,
    **{f"2026-{m:02d}": 3.75 for m in range(1, 9)},
    "2026-09": 3.75,  # Official MPC decision published 17 September 2026
}

# BoE IADB series IUM2WTL: monthly quoted 2-year fixed 95% LTV mortgage rates.
# Aggregate historic statistics, not live lender offers or individual quotes.
QUOTED_2Y_95_LTV = (
    ("2025-09", 5.03), ("2025-10", 5.00), ("2025-11", 4.91),
    ("2025-12", 4.83), ("2026-01", 4.80), ("2026-02", 4.82),
    ("2026-03", 5.23), ("2026-04", 5.80), ("2026-05", 5.63),
    ("2026-06", 5.54), ("2026-07", 5.48), ("2026-08", 5.52),
    ("2026-09", 5.70),
)

@lru_cache(maxsize=1)
def load_rates() -> tuple[tuple[str, float], ...]:
    """Use the legacy CSV Bank_Rate column, without discarding rows for other missing columns."""
    values: dict[str, float] = {}
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            date = datetime.strptime(row["Date"], "%d/%m/%Y")
            raw = row["Bank_Rate"]
            if raw:
                rate = float(raw) * 100  # legacy file stores rates as fractions
                if not (0 <= rate <= 25):
                    raise ValueError("Historical rate out of range")
                values[date.strftime("%Y-%m")] = round(rate, 4)
    values.update(BOE_VERIFIED)
    result = tuple(sorted(values.items()))
    if len(result) < 120:
        raise RuntimeError("Insufficient historical data")
    return result


def features(series: list[float]) -> list[float]:
    """Predict from observed lagged Bank Rates only; never use unavailable future mortgage data."""
    recent = series[-6:]
    return [
        series[-1], series[-2], series[-3],
        mean(recent[-3:]), mean(recent),
        series[-1] - series[-2],
    ]


def training_rows(series: list[float]):
    x, y = [], []
    for end in range(6, len(series)):
        x.append(features(series[:end]))
        y.append(series[end])
    return x, y


def train_model(values: list[float]) -> Ridge:
    x, y = training_rows(values)
    return Ridge(alpha=10.0).fit(x, y)


def mae(actual: list[float], predicted: list[float]) -> float:
    return mean(abs(a - p) for a, p in zip(actual, predicted))


def next_month(period: str, delta: int) -> str:
    year, month = (int(part) for part in period.split("-"))
    total = year * 12 + month - 1 + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


@lru_cache(maxsize=1)
def model_report() -> dict:
    observations = load_rates()
    rates = [point[1] for point in observations]
    actual: list[float] = []
    naive: list[float] = []
    machine: list[float] = []

    # Walk-forward one-step evaluation on the last 24 observed months.
    # Each prediction is trained only on data available before that month.
    for end in range(len(rates) - 24, len(rates)):
        past = rates[:end]
        actual.append(rates[end])
        naive.append(past[-1])
        fitted = train_model(past)
        machine.append(max(0.0, min(20.0, float(fitted.predict([features(past)])[0]))))

    naive_mae = mae(actual, naive)
    machine_mae = mae(actual, machine)
    use_ml = machine_mae < naive_mae * 0.90
    errors = [abs(a - b) for a, b in zip(actual, machine if use_ml else naive)]
    # This is an illustrative uncertainty band, NOT a statistically calibrated CI.
    ordered = sorted(errors)
    error_band = ordered[min(len(ordered) - 1, int(len(ordered) * 0.9))]
    return {
        "strategy": "lagged_ridge" if use_ml else "last_observation_baseline",
        "walk_forward_months": len(actual),
        "model_mae_percentage_points": round(machine_mae, 4),
        "baseline_mae_percentage_points": round(naive_mae, 4),
        "chosen_mae_percentage_points": round(machine_mae if use_ml else naive_mae, 4),
        "illustrative_error_band": error_band,
        "last_observation": observations[-1][0],
        "last_observed_rate_percent": observations[-1][1],
        "verified_official_updates_through": "2026-09",
    }


class MortgageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    property_price: float = Field(gt=10000, le=10000000, allow_inf_nan=False)
    deposit: float = Field(ge=0, le=10000000, allow_inf_nan=False)
    annual_rate: float = Field(ge=0, le=25, allow_inf_nan=False)
    term_years: int = Field(ge=5, le=40)

    @model_validator(mode="after")
    def check_deposit(self):
        if self.deposit >= self.property_price:
            raise ValueError("Deposit must be smaller than the property price")
        return self


def calculate(input_data: MortgageInput) -> dict:
    principal = input_data.property_price - input_data.deposit
    months = input_data.term_years * 12
    monthly_rate = input_data.annual_rate / 1200
    if monthly_rate == 0:
        monthly_payment = principal / months
    else:
        # Stable repayment formula avoiding unnecessary intermediate powers.
        monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-months))
    total_repaid = monthly_payment * months
    return {
        "property_price": round(input_data.property_price, 2),
        "deposit": round(input_data.deposit, 2),
        "loan_amount": round(principal, 2),
        "loan_to_value_percent": round(principal / input_data.property_price * 100, 2),
        "annual_rate_percent": round(input_data.annual_rate, 3),
        "term_years": input_data.term_years,
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_repaid - principal, 2),
        "total_repaid": round(total_repaid, 2),
        "note": "Illustrative capital-and-interest repayment. Fees, taxes, insurance and variable-rate changes excluded.",
    }


APP_ENV = os.getenv("APP_ENV", "development").lower()
if APP_ENV == "production":
    origin_config = os.getenv("ALLOWED_ORIGINS", "")
    if not origin_config or "*" in origin_config or "http://" in origin_config:
        raise RuntimeError("Production requires specific HTTPS ALLOWED_ORIGINS without wildcards")

app = FastAPI(
    title="Mortgage Intelligence API", version=VERSION,
    docs_url="/docs" if APP_ENV == "development" else None,
    redoc_url=None, openapi_url="/openapi.json" if APP_ENV == "development" else None,
)
origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )




@app.middleware("http")
async def gated_demo_access(request: Request, call_next):
    """Temporary synthetic-data demo gate; never use for real borrower records."""
    if os.getenv("APP_ENV", "development").lower() == "development":
        return await call_next(request)
    expected_user = os.getenv("DEMO_USER", "")
    expected_pass = os.getenv("DEMO_PASSWORD", "")
    if not expected_user or len(expected_pass) < 24:
        return JSONResponse(
            {"detail": "Private demo unavailable until access protection is configured"},
            status_code=503,
        )
    supplied = request.headers.get("authorization", "")
    username = password = ""
    if supplied.lower().startswith("basic "):
        try:
            pair = base64.b64decode(supplied.split(" ", 1)[1], validate=True).decode("utf-8")
            username, password = pair.split(":", 1)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            pass
    if not (hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_pass)):
        return JSONResponse(
            {"detail": "Private preview: authentication required"},
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Mortgage Intelligence Private Demo"'},
        )
    return await call_next(request)


@app.middleware("http")
async def response_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


class PortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """No PII fields; 1-50 anonymised mortgage scenarios accepted."""
    mortgages: list[MortgageInput] = Field(min_length=1, max_length=50)


@app.get("/api/market/quoted-mortgage-rates")
def quoted_mortgage_rates():
    return {
        "series_code": "IUM2WTL",
        "name": "UK monthly quoted two-year fixed mortgage rate at 95% LTV",
        "unit": "percent",
        "observation_type": "historical published market aggregate, not lender offer",
        "latest_period": QUOTED_2Y_95_LTV[-1][0],
        "source": "Bank of England IADB (UK Open Government Licence)",
        "source_url": "https://www.bankofengland.co.uk/boeapps/database/",
        "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "is_live": False,
        "observations": [{"period": date, "rate": rate} for date, rate in QUOTED_2Y_95_LTV],
        "warning": "This aggregate is not a live mortgage offer or an individual borrower's eligibility estimate.",
    }


@app.post("/api/broker/portfolio-scenarios")
def portfolio_scenarios(payload: PortfolioRequest):
    """Stateless aggregate sensitivity, intended only for synthetic or anonymised scenarios."""
    rows = []
    for shift in (-1.0, 0.0, 1.0, 2.0):
        monthly_total = 0.0
        for mortgage in payload.mortgages:
            assumed_rate = max(0.0, min(25.0, mortgage.annual_rate + shift))
            case = mortgage.model_copy(update={"annual_rate": assumed_rate})
            monthly_total += calculate(case)["monthly_payment"]
        rows.append({"shift_percentage_points": shift, "aggregate_monthly_repayment": round(monthly_total, 2)})
    baseline = rows[1]["aggregate_monthly_repayment"]
    for row in rows:
        row["monthly_change_from_baseline"] = round(row["aggregate_monthly_repayment"] - baseline, 2)
    return {
        "mortgages_count": len(payload.mortgages),
        "scenarios": rows,
        "source": "Provided hypothetical scenarios; application does not persist request bodies",
        "note": "No advice, affordability assessment, risk score, credit decision or lender portfolio forecast.",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/api/history")
def history(limit: int = Query(120, ge=12, le=400)):
    data = load_rates()
    return {
        "unit": "percent",
        "source": "Legacy UK rates CSV to Oct 2023; BoE IADB to Aug 2026 plus official Sep 2026 MPC decision",
        "source_url": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/september-2026",
        "latest_period": data[-1][0],
        "points": [{"period": date, "rate": rate} for date, rate in data[-limit:]],
    }


@app.get("/api/forecast")
def forecast(months: int = Query(12, ge=1, le=12)):
    report = model_report()
    observed = load_rates()
    generated = [p[1] for p in observed]
    model = train_model(generated) if report["strategy"] == "lagged_ridge" else None
    predictions = []
    for horizon in range(1, months + 1):
        value = float(model.predict([features(generated)])[0]) if model else generated[-1]
        value = max(0.0, min(20.0, value))
        band = max(0.10, report["illustrative_error_band"]) * math.sqrt(horizon)
        predictions.append({
            "period": next_month(observed[-1][0], horizon),
            "rate": round(value, 3),
            "illustrative_low": round(max(0.0, value - band), 3),
            "illustrative_high": round(min(20.0, value + band), 3),
        })
        generated.append(value)
    return {
        "series": "Bank of England Bank Rate, not lender mortgage rates",
        "status": "experimental",
        "model": report,
        "predictions": predictions,
        "warning": "Not a live rate quote, a calibrated confidence interval or financial advice. Economic shocks and policy decisions are not predictable from these historical rates alone.",
    }


@app.post("/api/mortgage/calculate")
def mortgage_calculate(input_data: MortgageInput):
    return calculate(input_data)


@app.post("/api/mortgage/compare")
def mortgage_compare(input_data: MortgageInput):
    rows = []
    for shift in (-1, -0.5, 0, 0.5, 1):
        scenario = input_data.model_copy(update={"annual_rate": min(25, max(0, input_data.annual_rate + shift))})
        computed = calculate(scenario)
        rows.append({
            "change_percentage_points": shift,
            "annual_rate_percent": computed["annual_rate_percent"],
            "monthly_payment": computed["monthly_payment"],
            "total_interest": computed["total_interest"],
        })
    return {
        "scenarios": rows,
        "note": "Hypothetical rate scenarios, not mortgage offers or rate forecasts.",
    }

# If the React bundle was built, serve it from this API origin behind the same gate.
DEMO_STATIC_ROOT = Path(__file__).resolve().parents[1] / "static"
if DEMO_STATIC_ROOT.is_dir():
    app.mount("/", StaticFiles(directory=DEMO_STATIC_ROOT, html=True), name="demo")
