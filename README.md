# Sales Forecasting & Trend Analysis Using Machine Learning
**B.Sc. Data Science Final Year Project**

---

## 📌 1. Project Overview & Objectives
This project implements an end-to-end data science and machine learning pipeline that analyzes historical transactional sales data, uncovers seasonality and purchasing patterns, and forecasts future sales with confidence intervals.

### Synopsis Objectives Accomplished:
1. **Dataset Collection & Preparation**: 10,219 historical sales records containing all 15 required transactional parameters.
2. **Relational MySQL Database**: Relational schema (`customers`, `products`, `sales_transactions`) managed via MySQL 8.0 & PyMySQL.
3. **Data Preprocessing & Cleaning**: Outlier detection (IQR), data type normalization, zero missing values, and chronological indexing.
4. **Exploratory Data Analysis (EDA)**: Statistical profiling, monthly/yearly trends, category performance, city-wise breakdowns, and profit margins.
5. **Data Visualizations**: High-resolution charts generated with Matplotlib & Seaborn, paired with interactive Chart.js widgets.
6. **Machine Learning Model Training**: Supervised regression using:
   - **Linear Regression**
   - **Decision Tree Regression**
   - **Random Forest Regression** (Best Model)
7. **Model Evaluation & Comparison**: Quantitative benchmarking using **MAE**, **RMSE**, and **R² Score**.
8. **Interactive Django Web Application**: A modern, responsive dashboard with KPI summary cards, dynamic multi-horizon forecasting, EDA visual gallery, model comparison screen, searchable transaction ledger, and strategic business recommendations.

---

## 🗂️ 2. Dataset Schema (All 15 Required Parameters)

| # | Parameter | Data Type | Description |
|---|-----------|-----------|-------------|
| 1 | `Sale ID` | VARCHAR(50) | Unique transaction identifier |
| 2 | `Customer ID` | VARCHAR(50) | Unique customer identifier |
| 3 | `Customer Name` | VARCHAR(150) | Name of the purchaser |
| 4 | `Product ID` | VARCHAR(50) | Unique product SKU |
| 5 | `Product Name` | VARCHAR(255) | Name of the product item |
| 6 | `Product Category` | VARCHAR(100) | Retail category (Electronics, Fashion, Home, Groceries, Beauty, Sports) |
| 7 | `Sale Date` | DATE | Date of transaction purchase |
| 8 | `Quantity Sold` | INT | Number of units purchased |
| 9 | `Unit Price` | DECIMAL(10,2) | Price per single unit (₹) |
| 10 | `Discount` | DECIMAL(5,2) | Discount percentage applied (%) |
| 11 | `Total Sales Amount`| DECIMAL(12,2) | Final transaction amount (₹) |
| 12 | `Cost Price` | DECIMAL(12,2) | Wholesale cost price (₹) |
| 13 | `Profit` | DECIMAL(12,2) | Net profit realized (₹) |
| 14 | `Payment Method` | VARCHAR(50) | UPI, Credit Card, Debit Card, Net Banking, COD |
| 15 | `Customer City` | VARCHAR(100) | Metropolitan city (Mumbai, Pune, Bengaluru, Delhi, etc.) |
| 16 | `Customer State` | VARCHAR(100) | Indian state |

---

## 🏗️ 3. Project Directory Architecture

```
Sales_Forecasting_ML/
├── dataset/
│   ├── generate_dataset.py       # Script to generate realistic historical sales data
│   └── sales_data.csv            # 10,219 transactional records
├── database/
│   ├── schema.sql                # MySQL relational DDL statements
│   ├── db_connection.py          # PyMySQL connection manager and DataFrame fetcher
│   └── setup_mysql.py            # Initializes database and populates records
├── ml_engine/
│   ├── eda.py                    # Preprocessing audit and Matplotlib/Seaborn plot generator
│   ├── feature_engineering.py    # Temporal, lag, and rolling statistics extraction
│   ├── train_models.py           # Trains & evaluates Linear Reg, Decision Tree, Random Forest
│   └── forecast.py               # Multi-step recursive forecasting inference engine
├── saved_models/
│   ├── linear_regression.joblib
│   ├── decision_tree_regression.joblib
│   ├── random_forest_regression.joblib
│   ├── best_model.joblib         # Top-performing serialized model
│   └── metrics.json              # MAE, RMSE, R2, and feature importance metadata
├── static_plots/                 # High-resolution generated charts
│   ├── monthly_sales_trend.png
│   ├── category_sales.png
│   ├── top_products.png
│   ├── profit_analysis.png
│   ├── city_sales.png
│   ├── sales_growth.png
│   └── historical_vs_forecast.png
├── sales_web/                    # Django web application
│   ├── manage.py
│   ├── sales_web/
│   │   ├── settings.py           # Configured with MySQL backend
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── dashboard/
│       ├── models.py             # Django ORM mapped to MySQL tables
│       ├── views.py              # Views & API endpoints
│       ├── urls.py
│       ├── static/
│       │   ├── css/custom.css
│       │   └── plots/
│       └── templates/dashboard/
│           ├── base.html
│           ├── dashboard.html    # Executive overview & KPIs
│           ├── forecast.html     # Interactive ML forecast engine
│           ├── eda.html          # EDA gallery & statistics
│           ├── models.html       # Quantitative model comparison
│           ├── transactions.html # Searchable ledger
│           └── insights.html     # Strategic business recommendations
├── requirements.txt
├── run_server.bat                # 1-click launch batch script
└── README.md
```

---

## 🤖 4. Machine Learning Model Evaluation & Results

Out-of-sample empirical testing performed on a chronological 80% Train / 20% Test split:

| Model | MAE (Mean Absolute Error) | RMSE (Root Mean Sq Error) | R² Score | Selection |
|---|---|---|---|---|
| **Random Forest Regression** | **Rs. 26,050.55** | **Rs. 33,895.93** | **16.59%** | ★ **Selected Best Model** |
| **Linear Regression** | Rs. 28,453.65 | Rs. 34,869.24 | 11.73% | Evaluated |
| **Decision Tree Regression**| Rs. 27,430.29 | Rs. 37,357.05 | -1.32% | Evaluated |

---

## 🚀 5. How to Run the Project

### Option A: Quick 1-Click Launch (Recommended)
Simply double click `run_server.bat` in the root folder, or in PowerShell:
```powershell
.\run_server.bat
```
Then open your browser at: **`http://127.0.0.1:8000/`**

---

### Option B: Manual Step-by-Step Execution

1. **Populate MySQL Database**:
   ```bash
   python database\setup_mysql.py
   ```

2. **Run Exploratory Data Analysis & Generate Visualizations**:
   ```bash
   python ml_engine\eda.py
   ```

3. **Train Machine Learning Models & Evaluate**:
   ```bash
   python ml_engine\train_models.py
   ```

4. **Start Django Web Server**:
   ```bash
   cd sales_web
   python manage.py runserver 127.0.0.1:8000
   ```
