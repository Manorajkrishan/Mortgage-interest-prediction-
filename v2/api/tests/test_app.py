import math

from fastapi.testclient import TestClient

from v2.api.app import MortgageInput, calculate, load_rates, model_report, next_month

client = TestClient(__import__("v2.api.app", fromlist=["app"]).app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_history_keeps_rows_with_missing_unrelated_columns():
    data = load_rates()
    assert len(data) >= 330
    assert ("1999-02", 5.5) in data
    assert data[-1] == ("2026-08", 3.75)


def test_month_rollover():
    assert next_month("2025-12", 2) == "2026-02"


def test_repayment_math_and_zero_rate():
    args = dict(property_price=300000, deposit=60000, term_years=25)
    regular = calculate(MortgageInput(**args, annual_rate=5))
    zero = calculate(MortgageInput(**args, annual_rate=0))
    assert 1402 < regular["monthly_payment"] < 1404
    assert zero["monthly_payment"] == 800.0
    assert regular["total_interest"] > 0
    assert regular["loan_to_value_percent"] == 80.0


def test_invalid_inputs_cannot_be_submitted():
    base = dict(property_price=300000, deposit=60000, annual_rate=5, term_years=25)
    for bad in [dict(deposit=350000), dict(annual_rate=-1), dict(term_years=0)]:
        response = client.post("/api/mortgage/calculate", json={**base, **bad})
        assert response.status_code == 422


def test_endpoint_calculate_and_compare():
    payload = dict(property_price=300000, deposit=60000, annual_rate=5, term_years=25)
    assert client.post("/api/mortgage/calculate", json=payload).status_code == 200
    scenarios = client.post("/api/mortgage/compare", json=payload).json()["scenarios"]
    assert len(scenarios) == 5
    assert scenarios[0]["monthly_payment"] < scenarios[-1]["monthly_payment"]


def test_forecast_is_temporal_and_marked_experimental():
    report = model_report()
    assert report["walk_forward_months"] == 24
    response = client.get("/api/forecast?months=3")
    assert response.status_code == 200
    values = response.json()
    assert values["status"] == "experimental"
    assert values["predictions"][0]["period"] == "2026-09"
    assert len(values["predictions"]) == 3
    assert all(math.isfinite(x["rate"]) for x in values["predictions"])
    assert values["series"].startswith("Bank of England")


def test_forecast_bounds():
    assert client.get("/api/forecast?months=13").status_code == 422
    assert client.get("/api/history?limit=2").status_code == 422
