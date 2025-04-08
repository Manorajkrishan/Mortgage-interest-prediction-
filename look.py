from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from prophet import Prophet

app = Flask(__name__)
CORS(app)

# --- Data Loading and Preprocessing ---
data = pd.read_csv('uk.csv')
data['Date'] = pd.to_datetime(data['Date'])
data = data.dropna()

# Feature selection
features = [
    'Fixed_Rate_2y_95%_LTV',
    'Fixed_Rate_2y_75%_LTV',
    'Tracker',
    'Variable Rate',
    'LIBOR_3m',
    'Gov_Bond_Yield_10y'
]
X = data[features]
y = data['Bank_Rate']

# Scale features for Decision Tree
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- Train Decision Tree Model ---
tree_model = DecisionTreeRegressor(random_state=42)
tree_model.fit(X_scaled, y)

# --- Train Prophet Model with Regressors ---
prophet_data = data[['Date', 'Bank_Rate'] + features].rename(columns={'Date': 'ds', 'Bank_Rate': 'y'})
prophet_model = Prophet(yearly_seasonality=True)

# Add all extra regressors
for feature in features:
    prophet_model.add_regressor(feature)

prophet_model.fit(prophet_data)

# --- Tree Model Metrics ---
y_pred_tree = tree_model.predict(X_scaled)
mse_tree = mean_squared_error(y, y_pred_tree)
mae_tree = mean_absolute_error(y, y_pred_tree)
r2_tree = r2_score(y, y_pred_tree)

# --- Prediction Endpoint ---
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    input_features = data.get('features')  # List of 6 numerical values
    input_date = pd.to_datetime(data.get('date'))  # YYYY-MM-DD format

    # --- Decision Tree Prediction ---
    input_df = pd.DataFrame([input_features], columns=features)
    input_scaled = scaler.transform(input_df)
    tree_prediction = tree_model.predict(input_scaled)[0]

    # --- Prophet Prediction with Regressors ---
    future_df = pd.DataFrame({'ds': [input_date]})
    for i, feature in enumerate(features):
        future_df[feature] = [input_features[i]]

    forecast_result = prophet_model.predict(future_df)
    prophet_prediction = max(0, forecast_result['yhat'].values[0])
    prophet_lower = max(0, forecast_result['yhat_lower'].values[0])
    prophet_upper = max(0, forecast_result['yhat_upper'].values[0])

    # --- Combine Predictions ---
    combined_rate = (
        0.6 * prophet_prediction + 0.4 * tree_prediction
        if prophet_prediction > 0
        else tree_prediction
    )

    return jsonify({
        'tree_prediction': round(tree_prediction, 3),
        'prophet_prediction': round(prophet_prediction, 3),
        'combined_rate': round(combined_rate, 3),
        'confidence_interval': [round(prophet_lower, 3), round(prophet_upper, 3)],
        'tree_metrics': {
            'mse': round(mse_tree, 4),
            'mae': round(mae_tree, 4),
            'r2': round(r2_tree, 4)
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
