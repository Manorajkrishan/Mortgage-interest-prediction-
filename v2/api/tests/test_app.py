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
    assert data[-1] == ("2026-09", 3.75)


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
    assert values["predictions"][0]["period"] == "2026-10"
    assert len(values["predictions"]) == 3
    assert all(math.isfinite(x["rate"]) for x in values["predictions"])
    assert values["series"].startswith("Bank of England")


def test_forecast_bounds():
    assert client.get("/api/forecast?months=13").status_code == 422
    assert client.get("/api/history?limit=2").status_code == 422


def test_market_series_are_non_live_and_attributed():
    response = client.get("/api/market/quoted-mortgage-rates")
    assert response.status_code == 200
    result = response.json()
    assert result["series_code"] == "IUM2WTL"
    assert result["is_live"] is False
    assert result["latest_period"] == "2026-09"
    assert result["observations"][-1] == {"period": "2026-09", "rate": 5.7}
    assert "not lender" in result["observation_type"]


def test_broker_portfolio_scenarios_limits_and_sensitivity():
    example = {"property_price": 300000, "deposit": 60000, "annual_rate": 5, "term_years": 25}
    response = client.post("/api/broker/portfolio-scenarios", json={"mortgages": [example, example]})
    assert response.status_code == 200
    result = response.json()
    assert result["mortgages_count"] == 2
    assert len(result["scenarios"]) == 4
    assert 2804 < result["scenarios"][1]["aggregate_monthly_repayment"] < 2810
    assert result["scenarios"][-1]["monthly_change_from_baseline"] > 0
    assert client.post("/api/broker/portfolio-scenarios", json={"mortgages": []}).status_code == 422
    assert client.post("/api/broker/portfolio-scenarios", json={"mortgages": [example] * 51}).status_code == 422


def test_security_headers():
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


def test_unknown_fields_rejected_before_any_financial_data_analysis():
    base = {"property_price": 300000, "deposit": 60000, "annual_rate": 5, "term_years": 25}
    unexpected = dict(base, customer_email="do-not-send@example.invalid")
    assert client.post("/api/mortgage/calculate", json=unexpected).status_code == 422
    assert client.post("/api/broker/portfolio-scenarios", json={"mortgages": [unexpected]}).status_code == 422


def test_private_preview_rejects_missing_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("DEMO_USER", "preview")
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    response = client.get("/api/history")
    assert response.status_code == 503


def test_private_preview_requires_correct_credentials(monkeypatch):
    import base64
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("DEMO_USER", "preview")
    monkeypatch.setenv("DEMO_PASSWORD", "unique-long-test-secret-only-1234567")
    assert client.get("/api/health").status_code == 401
    wrong = base64.b64encode(b"preview:wrong").decode()
    assert client.get("/api/health", headers={"Authorization": "Basic " + wrong}).status_code == 401
    valid = base64.b64encode(b"preview:unique-long-test-secret-only-1234567").decode()
    assert client.get("/api/health", headers={"Authorization": "Basic " + valid}).status_code == 200
