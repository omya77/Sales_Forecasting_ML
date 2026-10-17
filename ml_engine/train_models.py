"""
Model Training & Comparative Evaluation Pipeline
Trains Linear Regression, Decision Tree Regression, and Random Forest Regression.
Calculates MAE, RMSE, and R2 Score to empirically select and serialize the best model.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

# Add directories to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "database"))
sys.path.append(CURRENT_DIR)

from db_connection import fetch_sales_dataframe
from feature_engineering import prepare_daily_sales_features, FEATURE_COLUMNS, TARGET_COLUMN

SAVED_MODELS_DIR = os.path.join(PROJECT_ROOT, "saved_models")
PLOTS_DIR = os.path.join(PROJECT_ROOT, "static_plots")
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

def train_and_evaluate_all():
    print("=================================================================")
    print("     MACHINE LEARNING SALES FORECASTING MODEL PIPELINE")
    print("=================================================================")
    
    # 1. Load data
    try:
        print("Extracting sales data from MySQL database...")
        raw_df = fetch_sales_dataframe()
        print(f"Loaded {len(raw_df)} transactional records from MySQL.")
    except Exception as e:
        print(f"Database extraction failed ({e}), loading from CSV...")
        csv_path = os.path.join(PROJECT_ROOT, "dataset", "sales_data.csv")
        raw_df = pd.read_csv(csv_path)
        raw_df.columns = [col.lower().replace(" ", "_") for col in raw_df.columns]
        raw_df['sale_date'] = pd.to_datetime(raw_df['sale_date'])

    # 2. Engineer features
    print("Engineering temporal, lag, and rolling window features...")
    df_features = prepare_daily_sales_features(raw_df)
    print(f"Processed {len(df_features)} daily observation points with {len(FEATURE_COLUMNS)} features.")
    
    # 3. Train-Test Split (Chronological 80% / 20%)
    split_idx = int(len(df_features) * 0.8)
    train_df = df_features.iloc[:split_idx].copy()
    test_df = df_features.iloc[split_idx:].copy()
    
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]
    
    print(f"Train set: {len(X_train)} days ({train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')})")
    print(f"Test set:  {len(X_test)} days ({test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')})")
    
    # 4. Define Candidate Models
    models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regression": DecisionTreeRegressor(max_depth=6, min_samples_leaf=5, random_state=42),
        "Random Forest Regression": RandomForestRegressor(n_estimators=120, max_depth=10, min_samples_leaf=3, random_state=42)
    }
    
    results = {}
    predictions = {}
    
    print("\n--- Training & Evaluating Candidate Models ---")
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        predictions[name] = y_pred
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = root_mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {
            "model_name": name,
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "r2_score": round(float(r2), 4),
            "mae_formatted": f"Rs. {mae:,.2f}",
            "rmse_formatted": f"Rs. {rmse:,.2f}",
            "r2_percentage": f"{r2 * 100:.2f}%"
        }
        
        # Save individual model
        filename = name.lower().replace(" ", "_") + ".joblib"
        joblib.dump(model, os.path.join(SAVED_MODELS_DIR, filename))
        print(f"  {name} => MAE: Rs. {mae:,.2f} | RMSE: Rs. {rmse:,.2f} | R2: {r2*100:.2f}%")
        
    # 5. Determine Best Model based on R2 Score and RMSE
    best_name = max(results, key=lambda k: results[k]["r2_score"])
    best_model = models[best_name]
    print(f"\n>>> BEST PERFORMING MODEL: {best_name} (R2 Score: {results[best_name]['r2_percentage']})")
    
    # Save Best Model and Metadata
    joblib.dump(best_model, os.path.join(SAVED_MODELS_DIR, "best_model.joblib"))
    
    # Calculate feature importances if available
    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        for f, imp in zip(FEATURE_COLUMNS, best_model.feature_importances_):
            feature_importances[f] = round(float(imp), 4)
        feature_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))
    elif hasattr(best_model, "coef_"):
        for f, coef in zip(FEATURE_COLUMNS, best_model.coef_):
            feature_importances[f] = round(float(abs(coef)), 4)
            
    summary_meta = {
        "best_model_name": best_name,
        "models_evaluation": results,
        "feature_columns": FEATURE_COLUMNS,
        "feature_importances": feature_importances,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "last_trained_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    metrics_path = os.path.join(SAVED_MODELS_DIR, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary_meta, f, indent=4)
    print(f"Evaluation metrics saved to {metrics_path}")
    
    # 6. Generate Historical vs Forecasted Sales Chart (Step 5 & Step 8)
    print("Generating Historical vs Forecasted comparison chart...")
    plt.figure(figsize=(14, 6), dpi=300)
    plt.plot(test_df['date'], y_test, label='Actual Historical Sales', color='#0f172a', linewidth=2.0)
    plt.plot(test_df['date'], predictions["Random Forest Regression"], label='Random Forest Forecast', color='#10b981', linewidth=1.8, linestyle='--')
    plt.plot(test_df['date'], predictions["Linear Regression"], label='Linear Regression Forecast', color='#3b82f6', linewidth=1.5, linestyle=':')
    plt.plot(test_df['date'], predictions["Decision Tree Regression"], label='Decision Tree Forecast', color='#f59e0b', linewidth=1.5, linestyle='-.')
    
    plt.title('Actual vs Forecasted Sales Comparison (Evaluation Test Period)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Date', fontsize=11, fontweight='600')
    plt.ylabel('Daily Total Sales (₹)', fontsize=11, fontweight='600')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, loc='upper left')
    plt.tight_layout()
    chart_path = os.path.join(PLOTS_DIR, 'historical_vs_forecast.png')
    plt.savefig(chart_path)
    plt.close()
    print(f"Forecast comparison plot saved to {chart_path}")
    
    print("\n=================================================================")
    print("                MODEL TRAINING SUMMARY TABLE")
    print("=================================================================")
    print(f"{'Model':<28} | {'MAE (Rs)':<14} | {'RMSE (Rs)':<14} | {'R2 Score':<10}")
    print("-" * 75)
    for name, m in results.items():
        star = " * (Best)" if name == best_name else ""
        print(f"{name + star:<28} | {m['mae']:<14,.2f} | {m['rmse']:<14,.2f} | {m['r2_percentage']:<10}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    train_and_evaluate_all()
