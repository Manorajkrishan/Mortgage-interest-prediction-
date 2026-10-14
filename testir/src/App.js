import React, { useEffect, useState } from "react";
import "./App.css";

const API_BASE = (process.env.REACT_APP_API_BASE_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "")).replace(/\/$/, "");
const money = (n) => new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(Number(n || 0));
const moneyExact = (n) => new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(n || 0));
const percent = (n) => Number(n || 0).toFixed(2) + "%";

async function apiRequest(path, options) {
  const response = await fetch(API_BASE + path, options);
  if (!response.ok) {
    let reason = "Unable to complete this request";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") reason = body.detail;
    } catch (_) { /* fallback message */ }
    throw new Error(reason);
  }
  return response.json();
}

function localPayment({ property_price, deposit, annual_rate, term_years }) {
  const principal = property_price - deposit;
  const months = term_years * 12;
  const rate = annual_rate / 1200;
  const payment = rate === 0 ? principal / months : principal * rate / (1 - Math.pow(1 + rate, -months));
  return {
    loan_amount: principal,
    property_price, deposit, term_years,
    loan_to_value_percent: (principal / property_price) * 100,
    monthly_payment: payment,
    total_interest: payment * months - principal,
    total_repaid: payment * months
  };
}

function localScenarios(form) {
  return [-1, -0.5, 0, 0.5, 1].map((change) => {
    const rate = Math.max(0, Number(form.annual_rate) + change);
    const output = localPayment({ ...form, annual_rate: rate });
    return {
      change_percentage_points: change,
      annual_rate_percent: rate,
      monthly_payment: output.monthly_payment,
      total_interest: output.total_interest
    };
  });
}

function RateChart({ history, outlook }) {
  if (!history.length) return <div className="chart-empty">Connect the API to load historical Bank Rate data.</div>;
  const observed = history.slice(-48);
  const predicted = outlook || [];
  const all = [...observed, ...predicted];
  const values = all.map((p) => Number(p.rate));
  const lowest = Math.max(0, Math.floor(Math.min(...values) - 0.6));
  const highest = Math.ceil(Math.max(...values) + 0.6);
  const width = 820, height = 278, left = 50, right = 24, top = 28, bottom = 38;
  const x = (i) => left + i * (width - left - right) / (all.length - 1);
  const y = (v) => top + (highest - v) / (highest - lowest || 1) * (height - top - bottom);
  const path = (points, offset) => points.map((point, i) => (i === 0 ? "M" : "L") + x(i + offset).toFixed(1) + "," + y(Number(point.rate)).toFixed(1)).join(" ");
  const historyLine = path(observed, 0);
  const predictedLine = predicted.length ? path([observed[observed.length - 1], ...predicted], observed.length - 1) : "";
  const markers = [0, Math.round((observed.length - 1) / 2), observed.length - 1, all.length - 1];
  return <svg className="rate-chart" viewBox={"0 0 " + width + " " + height} role="img" aria-label="Historical Bank Rate with an experimental future outlook">
    {[0, 1, 2, 3, 4].map(i => {
      const value = lowest + (highest - lowest) * i / 4;
      return <g key={i}>
        <line x1={left} y1={y(value)} x2={width - right} y2={y(value)} stroke="#293c54" strokeDasharray="4 8" />
        <text x="8" y={y(value) + 4} fill="#8ea4bd" fontSize="11">{value.toFixed(1)}%</text>
      </g>;
    })}
    {predicted.length > 0 && <line x1={x(observed.length - 1)} x2={x(observed.length - 1)} y1={top} y2={height - bottom} stroke="#60748e" strokeDasharray="5 5" />}
    <path d={historyLine} fill="none" stroke="#79a8ff" strokeWidth="3.4" strokeLinejoin="round" strokeLinecap="round" />
    {predictedLine && <path d={predictedLine} fill="none" stroke="#7de6bf" strokeWidth="3.4" strokeDasharray="7 7" strokeLinejoin="round" strokeLinecap="round" />}
    <circle cx={x(observed.length - 1)} cy={y(observed[observed.length - 1].rate)} r="5" fill="#79a8ff" stroke="#12213a" strokeWidth="3" />
    {markers.filter((item, i) => markers.indexOf(item) === i).map(i =>
      <text key={i} textAnchor={i === 0 ? "start" : i === all.length - 1 ? "end" : "middle"} x={x(i)} y={height - 13} fill="#a8b9d0" fontSize="12">{all[i].period}</text>
    )}
  </svg>;
}

function App() {
  const [form, setForm] = useState({ property_price: "300000", deposit: "60000", annual_rate: "4.75", term_years: "25" });
  const [result, setResult] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [calculationSource, setCalculationSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [marketError, setMarketError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest("/api/history?limit=72"),
      apiRequest("/api/forecast?months=12")
    ]).then(([past, future]) => {
      if (active) { setHistory(past.points || []); setForecast(future); }
    }).catch(() => {
      if (active) setMarketError("Rate outlook unavailable: connect the secured backend to display sourced historical data.");
    });
    return () => { active = false; };
  }, []);

  const onField = (event) => setForm(previous => ({ ...previous, [event.target.name]: event.target.value }));

  const onCalculate = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    const fields = {
      property_price: Number(form.property_price),
      deposit: Number(form.deposit),
      annual_rate: Number(form.annual_rate),
      term_years: Number(form.term_years)
    };
    if (!(fields.property_price > 10000 && fields.property_price <= 10000000 &&
      fields.deposit >= 0 && fields.deposit < fields.property_price &&
      fields.annual_rate >= 0 && fields.annual_rate <= 25 &&
      Number.isInteger(fields.term_years) && fields.term_years >= 5 && fields.term_years <= 40)) {
      setError("Check the property price, deposit, interest rate (0–25%) and term (5–40 years).");
      setLoading(false);
      return;
    }
    try {
      const [calculation, comparison] = await Promise.all([
        apiRequest("/api/mortgage/calculate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) }),
        apiRequest("/api/mortgage/compare", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) })
      ]);
      setResult(calculation);
      setScenarios(comparison.scenarios);
      setCalculationSource("API calculation");
    } catch (_) {
      setResult(localPayment(fields));
      setScenarios(localScenarios(fields));
      setCalculationSource("Offline illustrative calculation • API unavailable");
    } finally {
      setLoading(false);
    }
  };

  const saveCSV = () => {
    if (!scenarios.length) return;
    const lines = [
      "Change (percentage points),Annual rate (%),Monthly repayment (GBP),Total interest (GBP)",
      ...scenarios.map(row => [row.change_percentage_points, row.annual_rate_percent, row.monthly_payment.toFixed(2), row.total_interest.toFixed(2)].join(","))
    ];
    const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "mortgage-scenario-comparison.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return <div className="site-shell">
    <header className="topbar wrap">
      <a href="#home" className="brand" aria-label="Mortgage Intelligence home">
        <span className="brand-mark">M<span>↗</span></span>
        <span>mortgage<span className="brand-light">intel</span><small>UK PROPERTY FINANCE</small></span>
      </a>
      <nav aria-label="Main menu">
        <a href="#calculator">Calculator</a>
        <a href="#scenarios">Rate scenarios</a>
        <a href="#outlook">Market outlook</a>
      </nav>
      <span className="top-status"><span className="status-dot"></span> Research beta</span>
    </header>

    <main id="home">
      <section className="hero wrap">
        <div className="hero-copy">
          <span className="eyebrow"><span className="eyebrow-line"></span> PROPERTY FINANCE, MADE CLEARER</span>
          <h1>Understand the numbers.<br /><em>Own your next move.</em></h1>
          <p>Explore mortgage repayments, compare interest-rate scenarios and examine an experimental Bank of England rate outlook — all in one place.</p>
          <div className="hero-actions">
            <a className="primary-button" href="#calculator">Explore your mortgage <span aria-hidden="true">↗</span></a>
            <a className="simple-link" href="#outlook">Explore the market <span aria-hidden="true">→</span></a>
          </div>
          <p className="subtle-note">Independent educational tool. No lender offers or mortgage advice.</p>
        </div>
        <div className="hero-panel" aria-label="Product overview">
          <div className="panel-top"><span className="dot-grid">✦</span> MARKET INTELLIGENCE <span className="pill">BETA</span></div>
          <div className="panel-graphic"><div className="graphic-building">▱</div><span className="graphic-ticker">REPAYMENT INSIGHTS</span><span className="graphic-number">£1,402<span>/mo</span></span><div className="graphic-bars">{[34,52,44,68,61,78,70,90,77,100].map((h,i)=><span key={i} style={{height:h+"%"}}></span>)}</div></div>
          <div className="panel-bottom"><span>PLAN WITH CLARITY</span><span>UK · GBP</span></div>
          <div className="illustration-footnote">Sample illustration only — not a personalised quote.</div>
        </div>
      </section>

      <section className="info-strip wrap" aria-label="Platform highlights">
        <div><strong>01</strong><span>Repayment modelling</span></div>
        <div><strong>02</strong><span>Rate sensitivity analysis</span></div>
        <div><strong>03</strong><span>Transparent model evaluation</span></div>
      </section>

      <section className="workarea wrap" id="calculator">
        <div className="section-heading"><div><span className="eyebrow">MORTGAGE LAB</span><h2>Run the numbers</h2><p>See how a property price, deposit, term and illustrative rate affect repayments.</p></div><span className="section-index">01 / CALCULATE</span></div>
        <div className="calculator-grid">
          <form className="calc-card" onSubmit={onCalculate}>
            <div className="card-heading"><div className="round-icon">⌂</div><div><h3>Your mortgage details</h3><p>Adjust the inputs to explore a scenario</p></div></div>
            <div className="field-grid">
              <label className="field"><span>Property price</span><div className="input-shell"><span>£</span><input name="property_price" type="number" value={form.property_price} onChange={onField} min="10001" max="10000000" step="1000" required /></div></label>
              <label className="field"><span>Deposit</span><div className="input-shell"><span>£</span><input name="deposit" type="number" value={form.deposit} onChange={onField} min="0" step="1000" required /></div></label>
              <label className="field"><span>Annual mortgage rate</span><div className="input-shell"><input name="annual_rate" type="number" value={form.annual_rate} onChange={onField} min="0" max="25" step="0.05" required /><span>%</span></div></label>
              <label className="field"><span>Mortgage term</span><div className="input-shell"><input name="term_years" type="number" value={form.term_years} onChange={onField} min="5" max="40" step="1" required /><span>years</span></div></label>
            </div>
            <div className="form-hint">The example rate is an input, not a live lender rate.</div>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="primary-button calculate-button" type="submit" disabled={loading}>{loading ? "Calculating…" : "Calculate repayment"} <span>→</span></button>
          </form>

          <div className="results-card" aria-live="polite">
            <span className="result-label">ESTIMATED MONTHLY REPAYMENT</span>
            <div className="big-result">{result ? moneyExact(result.monthly_payment) : "£—"}<span> / month</span></div>
            <p className="result-explanation">Based on a capital-and-interest repayment mortgage.</p>
            <div className="result-divider"></div>
            <div className="result-row"><span>Borrowing amount</span><strong>{result ? money(result.loan_amount) : "—"}</strong></div>
            <div className="result-row"><span>Loan to value</span><strong>{result ? percent(result.loan_to_value_percent) : "—"}</strong></div>
            <div className="result-row"><span>Total interest</span><strong>{result ? money(result.total_interest) : "—"}</strong></div>
            <div className="result-row"><span>Total repayments</span><strong>{result ? money(result.total_repaid) : "—"}</strong></div>
            <div className="result-footnote">{calculationSource || "Enter your figures and select Calculate repayment."}</div>
          </div>
        </div>
      </section>

      <section className="workarea wrap" id="scenarios">
        <div className="section-heading"><div><span className="eyebrow">RATE SENSITIVITY</span><h2>What if rates change?</h2><p>Compare hypothetical interest rates against the same loan amount and term.</p></div><span className="section-index">02 / COMPARE</span></div>
        <div className="scenario-card">
          {scenarios.length ? <><div className="table-scroll"><table><thead><tr><th>Rate shift</th><th>Illustrative rate</th><th>Monthly payment</th><th>Lifetime interest</th></tr></thead><tbody>{scenarios.map((row) => <tr key={row.change_percentage_points} className={row.change_percentage_points === 0 ? "baseline-row" : ""}><td>{row.change_percentage_points === 0 ? "Base scenario" : (row.change_percentage_points > 0 ? "+" : "") + row.change_percentage_points.toFixed(1) + " pp"}</td><td>{percent(row.annual_rate_percent)}</td><td>{moneyExact(row.monthly_payment)}</td><td>{money(row.total_interest)}</td></tr>)}</tbody></table></div><div className="scenario-footer"><span>Illustrative scenarios, not predicted lender rates.</span><button className="text-button" type="button" onClick={saveCSV}>Export CSV ↓</button></div></> :
          <div className="empty-results">Calculate a mortgage to compare five hypothetical interest-rate scenarios.</div>}
        </div>
      </section>

      <section className="workarea wrap outlook-section" id="outlook">
        <div className="section-heading"><div><span className="eyebrow">UK RATE INTELLIGENCE</span><h2>See the bigger picture</h2><p>Historical Bank Rate and an experimental, evaluated statistical outlook.</p></div><span className="section-index">03 / EXPLORE</span></div>
        <div className="outlook-card">
          <div className="outlook-top"><div><h3>Bank of England Bank Rate</h3><p>Official policy rate — not a retail mortgage offer</p></div><div className="chart-legend"><span><i className="legend-history"></i> Historical</span><span><i className="legend-forecast"></i> Experimental</span></div></div>
          <RateChart history={history} outlook={forecast?.predictions} />
          {forecast ? <>
            <div className="outlook-stats">
              <div><span>Last observed rate</span><strong>{percent(forecast.model.last_observed_rate_percent)}</strong><small>{forecast.model.last_observation}</small></div>
              <div><span>Selected method</span><strong className="small-metric">{forecast.model.strategy === "lagged_ridge" ? "Lagged ridge model" : "Persistence baseline"}</strong><small>Walk-forward evaluation</small></div>
              <div><span>Evaluation MAE</span><strong>{forecast.model.chosen_mae_percentage_points.toFixed(3)} pp</strong><small>{forecast.model.walk_forward_months} held-out observations</small></div>
            </div>
            <p className="outlook-warning">{forecast.warning} Uncertainty bounds are illustrative, not calibrated confidence intervals. Historical source verified only through {forecast.model.last_observation}.</p>
          </> : <p className="outlook-warning">{marketError || "Loading historical data and model report…"}</p>}
        </div>
      </section>
    </main>

    <footer className="footer wrap"><div className="footer-brand">mortgage<span>intel</span></div><p>Educational research beta. No live lender pricing, eligibility decisions or personal mortgage advice. Verify all figures independently with a qualified professional.</p><span>© 2026 Mortgage Intelligence · UK</span></footer>
  </div>;
}

export default App;
