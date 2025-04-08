import React, { useState } from "react";
import "./App.css";

function App() {
  const [features, setFeatures] = useState({
    Fixed_Rate_2y_95: "",
    Fixed_Rate_2y_75: "",
    Tracker: "",
    Variable: "",
    LIBOR: "",
    Gov_Bond: "",
  });

  const [date, setDate] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFeatures({ ...features, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const inputFeatures = Object.values(features).map((val) => parseFloat(val));

    if (inputFeatures.some(isNaN)) {
      setError("Please enter valid numbers for all fields.");
      setLoading(false);
      return;
    }

    const payload = { features: inputFeatures, date };

    try {
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setPrediction(data);
      } else {
        setError("Error fetching predictions. Please try again.");
      }
    } catch (error) {
      setError("Network error. Please check your connection.");
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1 className="title">Mortgage Rate Predictor 💰🏡</h1>

      <form onSubmit={handleSubmit} className="form">
        {Object.keys(features).map((key) => (
          <div key={key} className="input-group">
            <label>{key.replace(/_/g, " ")}:</label>
            <input
              type="number"
              name={key}
              value={features[key]}
              onChange={handleChange}
              step="0.01"
              required
            />
          </div>
        ))}

        <div className="input-group">
          <label>Date:</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Predicting..." : "Predict"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {prediction && (
        <div className="results">
          <h2>Prediction Results 📊</h2>
          <p><strong>Decision Tree Prediction:</strong> {prediction.tree_prediction.toFixed(2)}</p>
          <p><strong>Prophet Prediction:</strong> {prediction.prophet_prediction.toFixed(2)}</p>
          <p><strong>Combined Rate:</strong> {prediction.combined_rate.toFixed(2)}</p>

          <h3>📈 Decision Tree Model Metrics</h3>
          <p><strong>MSE:</strong> {prediction.tree_metrics.mse.toFixed(6)}</p>
          <p><strong>MAE:</strong> {prediction.tree_metrics.mae.toFixed(6)}</p>
          <p><strong>R² Score:</strong> {prediction.tree_metrics.r2.toFixed(6)}</p>
        </div>
      )}
    </div>
  );
}

export default App;
