"""
Sales Forecasting Inference Engine
Executes multi-step forward recursive forecasting using trained machine learning models.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "database"))
sys.path.append(CURRENT_DIR)

from db_connection import fetch_sales_dataframe
from feature_engineering import prepare_daily_sales_features, FEATURE_COLUMNS

SAVED_MODELS_DIR = os.path.join(PROJECT_ROOT, "saved_models")

def load_trained_model(model_name="best_model"):
    """Loads specified model from saved_models directory."""
    if not model_name.endswith(".joblib"):
        model_name = f"{model_name}.joblib"
    path = os.path.join(SAVED_MODELS_DIR, model_name)
    if not os.path.exists(path):
        path = os.path.join(SAVED_MODELS_DIR, "best_model.joblib")
    return joblib.load(path)

def load_metrics():
    """Loads metrics.json metadata."""
    metrics_path = os.path.join(SAVED_MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def forecast_future_sales(days_ahead=30, model_choice="best_model"):
    """
    Performs recursive forward forecasting for specified number of days.
    Returns daily forecast points with upper and lower bounds.
    """
    model = load_trained_model(model_choice)
    metrics = load_metrics()
    
    # 1. Fetch historical data
    try:
        raw_df = fetch_sales_dataframe()
    except Exception:
        csv_path = os.path.join(PROJECT_ROOT, "dataset", "sales_data.csv")
        raw_df = pd.read_csv(csv_path)
        raw_df.columns = [c.lower().replace(" ", "_") for c in raw_df.columns]
        raw_df['sale_date'] = pd.to_datetime(raw_df['sale_date'])
        
    df_features = prepare_daily_sales_features(raw_df)
    
    # Keep rolling buffer of historical daily total sales
    daily_history = list(df_features['total_sales'].values)
    last_date = pd.to_datetime(df_features['date'].iloc[-1])
    
    forecast_results = []
    current_date = last_date
    
    # Standard deviation of error from test set metrics (RMSE)
    rmse = 33895.0
    if metrics and "models_evaluation" in metrics:
        best_n = metrics.get("best_model_name", "Random Forest Regression")
        rmse = metrics["models_evaluation"].get(best_n, {}).get("rmse", 33895.0)
        
    for step in range(1, days_ahead + 1):
        current_date = current_date + pd.Timedelta(days=1)
        
        # Calendar features
        year = current_date.year
        month = current_date.month
        day = current_date.day
        dayofweek = current_date.dayofweek
        quarter = current_date.quarter
        is_weekend = int(dayofweek in [5, 6])
        is_month_start = int(current_date.is_month_start)
        is_month_end = int(current_date.is_month_end)
        is_festive = int(month in [10, 11, 12])
        
        # Lag features from buffer
        lag_1 = daily_history[-1]
        lag_2 = daily_history[-2] if len(daily_history) >= 2 else lag_1
        lag_7 = daily_history[-7] if len(daily_history) >= 7 else lag_1
        lag_14 = daily_history[-14] if len(daily_history) >= 14 else lag_7
        lag_30 = daily_history[-30] if len(daily_history) >= 30 else lag_14
        
        # Rolling stats from buffer
        last_7 = daily_history[-7:]
        rolling_mean_7 = float(np.mean(last_7))
        rolling_std_7 = float(np.std(last_7)) if len(last_7) > 1 else 0.0
        
        last_30 = daily_history[-30:]
        rolling_mean_30 = float(np.mean(last_30))
        rolling_std_30 = float(np.std(last_30)) if len(last_30) > 1 else 0.0
        
        # Construct feature vector
        feat_vector = pd.DataFrame([{
            'year': year,
            'month': month,
            'day': day,
            'dayofweek': dayofweek,
            'quarter': quarter,
            'is_weekend': is_weekend,
            'is_month_start': is_month_start,
            'is_month_end': is_month_end,
            'is_festive': is_festive,
            'lag_1': lag_1,
            'lag_2': lag_2,
            'lag_7': lag_7,
            'lag_14': lag_14,
            'lag_30': lag_30,
            'rolling_mean_7': rolling_mean_7,
            'rolling_std_7': rolling_std_7,
            'rolling_mean_30': rolling_mean_30,
            'rolling_std_30': rolling_std_30
        }])[FEATURE_COLUMNS]
        
        pred_val = float(model.predict(feat_vector)[0])
        pred_val = max(1000.0, pred_val) # Sales cannot be negative
        
        # Confidence interval (wider uncertainty as horizon increases)
        horizon_uncertainty = 1.0 + (step / days_ahead) * 0.4
        lower_bound = max(0.0, pred_val - (1.96 * rmse * horizon_uncertainty * 0.5))
        upper_bound = pred_val + (1.96 * rmse * horizon_uncertainty * 0.5)
        
        forecast_results.append({
            "step": step,
            "date": current_date.strftime("%Y-%m-%d"),
            "day_name": current_date.strftime("%A"),
            "predicted_sales": round(pred_val, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "is_weekend": bool(is_weekend)
        })
        
        # Append predicted value into recursive history buffer
        daily_history.append(pred_val)
        
    total_forecasted = sum(item["predicted_sales"] for item in forecast_results)
    avg_daily_forecast = total_forecasted / len(forecast_results) if forecast_results else 0.0
    
    return {
        "horizon_days": days_ahead,
        "model_used": model_choice,
        "start_forecast_date": (last_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        "end_forecast_date": current_date.strftime("%Y-%m-%d"),
        "total_forecasted_sales": round(total_forecasted, 2),
        "avg_daily_forecast": round(avg_daily_forecast, 2),
        "daily_breakdown": forecast_results
    }

if __name__ == "__main__":
    result = forecast_future_sales(days_ahead=14)
    print(f"14-Day Sales Forecast: Rs. {result['total_forecasted_sales']:,.2f}")
    for item in result["daily_breakdown"][:5]:
        print(f"  {item['date']} ({item['day_name']}): Rs. {item['predicted_sales']:,.2f}")
