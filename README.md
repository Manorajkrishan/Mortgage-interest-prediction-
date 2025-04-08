# 🏡 Mortgage Rate Predictor for the UK  
A comprehensive project designed to forecast **Bank of England base rates** using a combination of **time-series analysis (Prophet)** and **machine learning (Decision Tree Regressor)**. This project is aimed at providing reliable insights for **homebuyers, brokers, and financial analysts** to make informed mortgage-related decisions.  

---

## 🔍 Features  
- **Dual-Model Approach**:  
  Combines **Prophet** for trend-based forecasting and **Decision Tree Regressor** for feature-based predictions.  
- **User-Friendly API**:  
  Built with Flask, allowing seamless communication between the models and the React frontend.  
- **Interactive Interface**:  
  A React-based frontend for users to input custom dates and financial indicators and get predictions.  
- **Performance Metrics**:  
  Displays model performance using R², MAE, and MSE metrics.  

---

## 📊 Dataset  
The project uses a **UK mortgage rate dataset** spanning from **1999 to 2023**, including:  
- Fixed Rate (2 years, 95% LTV)  
- Fixed Rate (2 years, 75% LTV)  
- Tracker Rates  
- Variable Rates  
- LIBOR (3-month)  
- Government Bond Yield (10 years)  
- Bank of England Base Rate  

---

## ⚙️ Technologies Used  
- **Backend**: Flask, Python (Pandas, Scikit-learn, Prophet)  
- **Frontend**: React.js  
- **Database**: CSV file-based data storage  

---

## 🚀 How to Run the Project  
1. **Clone the Repository**:  
   ```bash  
   git clone https://github.com/your-username/mortgage-rate-predictor.git  
   cd mortgage-rate-predictor  
