@echo off
title Sales Forecasting & Trend Analysis ML System
color 0b
echo ===============================================================================
echo            SALES FORECASTING & TREND ANALYSIS USING MACHINE LEARNING
echo                     B.Sc. Data Science Final Year Project
echo ===============================================================================
echo.
echo [1/3] Checking MySQL Service & Database Connectivity...
python -c "import sys; sys.path.append('database'); from db_connection import get_db_connection; conn=get_db_connection(); print('  * MySQL Connection Established Successfully!'); conn.close()"
if %errorlevel% neq 0 (
    echo [ERROR] Could not connect to MySQL server. Please ensure MySQL80 is running.
    pause
    exit /b %errorlevel%
)
echo.
echo [2/3] Verifying Machine Learning Models...
if not exist "saved_models\best_model.joblib" (
    echo   * Saved models not found. Running ML training pipeline...
    python ml_engine\train_models.py
) else (
    echo   * Machine Learning models loaded (Random Forest, Decision Tree, Linear Reg).
)
echo.
echo [3/3] Launching Django Interactive Web Dashboard...
echo.
echo ===============================================================================
echo   Dashboard URL: http://127.0.0.1:8000/
echo   Press CTRL+C in this terminal window to stop the server.
echo ===============================================================================
echo.
cd sales_web
python manage.py runserver 127.0.0.1:8000
pause
