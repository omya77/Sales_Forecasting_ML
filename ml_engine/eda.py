"""
Exploratory Data Analysis (EDA) & Data Visualization Module
Performs data quality checks, statistical summarization, and generates
the required visual representations using Matplotlib and Seaborn.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Style settings for academic and professional presentation
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

# Add parent directory to path to import db_connection
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "database"))

try:
    from db_connection import fetch_sales_dataframe
except ImportError:
    fetch_sales_dataframe = None

PLOTS_DIR = os.path.join(PROJECT_ROOT, "static_plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def load_data():
    """Loads dataset from MySQL database with CSV fallback."""
    if fetch_sales_dataframe:
        try:
            print("Fetching sales data from MySQL database `sales_forecasting_db`...")
            df = fetch_sales_dataframe()
            print(f"Successfully loaded {len(df)} records from MySQL.")
            return df
        except Exception as e:
            print(f"MySQL fetch warning: {e}. Falling back to CSV dataset...")
            
    csv_path = os.path.join(PROJECT_ROOT, "dataset", "sales_data.csv")
    df = pd.read_csv(csv_path)
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    return df

def run_data_audit(df):
    """Checks for missing values, duplicates, and data consistency (Step 3)."""
    print("\n--- DATA PREPROCESSING & INTEGRITY AUDIT ---")
    print(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Missing values
    missing = df.isnull().sum()
    print("Missing Values Per Column:")
    print(missing[missing > 0] if missing.sum() > 0 else "  No missing values detected (100% complete).")
    
    # Duplicates
    duplicates = df.duplicated(subset=['sale_id']).sum()
    print(f"Duplicate Sale IDs: {duplicates}")
    
    # Negative/Invalid value validation
    invalid_sales = (df['total_sales_amount'] <= 0).sum()
    invalid_qty = (df['quantity_sold'] <= 0).sum()
    print(f"Invalid Sales Values (<=0): {invalid_sales}")
    print(f"Invalid Quantities (<=0): {invalid_qty}")
    
    # Outlier detection using IQR on Total Sales Amount
    Q1 = df['total_sales_amount'].quantile(0.25)
    Q3 = df['total_sales_amount'].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df['total_sales_amount'] < (Q1 - 1.5 * IQR)) | (df['total_sales_amount'] > (Q3 + 1.5 * IQR))]
    print(f"High-value Transaction Outliers (IQR method): {len(outliers)} rows ({len(outliers)/len(df)*100:.2f}%)")
    print("Audit completed successfully.\n")

def generate_eda_visualizations(df):
    """Generates and saves the 6 core visual representations (Step 4 & Step 5)."""
    print("Generating comprehensive EDA visualizations...")
    df['year_month'] = df['sale_date'].dt.to_period('M')
    
    # 1. Monthly Sales Trends
    plt.figure(figsize=(12, 5), dpi=300)
    monthly_sales = df.groupby('year_month')['total_sales_amount'].sum() / 1e5 # in Lakhs
    ax = monthly_sales.plot(kind='line', marker='o', color='#2563eb', linewidth=2.5, markersize=6)
    plt.title('Monthly Total Sales Trends (2023 - 2025)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=11, fontweight='600')
    plt.ylabel('Total Sales (₹ in Lakhs)', fontsize=11, fontweight='600')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    p1 = os.path.join(PLOTS_DIR, 'monthly_sales_trend.png')
    plt.savefig(p1)
    plt.close()
    print(f" Saved: {p1}")

    # 2. Category-wise Sales
    plt.figure(figsize=(10, 5), dpi=300)
    cat_sales = df.groupby('product_category')['total_sales_amount'].sum().sort_values(ascending=False) / 1e5
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
    bars = plt.bar(cat_sales.index, cat_sales.values, color=colors[:len(cat_sales)], edgecolor='#1e293b', width=0.6)
    plt.title('Total Sales by Product Category (₹ in Lakhs)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Category', fontsize=11, fontweight='600')
    plt.ylabel('Sales (₹ in Lakhs)', fontsize=11, fontweight='600')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0, f"₹{yval:.1f}L", ha='center', va='bottom', fontsize=9, fontweight='600')
    plt.tight_layout()
    p2 = os.path.join(PLOTS_DIR, 'category_sales.png')
    plt.savefig(p2)
    plt.close()
    print(f" Saved: {p2}")

    # 3. Top Selling Products
    plt.figure(figsize=(11, 6), dpi=300)
    top_prods = df.groupby('product_name')['total_sales_amount'].sum().sort_values(ascending=True).tail(8) / 1e5
    plt.barh(top_prods.index, top_prods.values, color='#0ea5e9', edgecolor='#0369a1', height=0.6)
    plt.title('Top 8 Revenue-Generating Products (₹ in Lakhs)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Total Revenue (₹ in Lakhs)', fontsize=11, fontweight='600')
    plt.ylabel('Product Name', fontsize=11, fontweight='600')
    for i, v in enumerate(top_prods.values):
        plt.text(v + 0.5, i, f"₹{v:.1f}L", va='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    p3 = os.path.join(PLOTS_DIR, 'top_products.png')
    plt.savefig(p3)
    plt.close()
    print(f" Saved: {p3}")

    # 4. Profit Analysis by Category
    plt.figure(figsize=(10, 5), dpi=300)
    profit_summary = df.groupby('product_category')[['total_sales_amount', 'profit']].sum() / 1e5
    profit_summary['profit_margin_%'] = (profit_summary['profit'] / profit_summary['total_sales_amount']) * 100
    profit_summary = profit_summary.sort_values(by='profit', ascending=False)
    
    x = np.arange(len(profit_summary))
    width = 0.35
    plt.bar(x - width/2, profit_summary['total_sales_amount'], width, label='Sales (₹ Lakhs)', color='#93c5fd')
    plt.bar(x + width/2, profit_summary['profit'], width, label='Profit (₹ Lakhs)', color='#10b981')
    plt.title('Revenue vs Net Profit by Category', fontsize=14, fontweight='bold', pad=15)
    plt.xticks(x, profit_summary.index, rotation=15)
    plt.ylabel('Amount (₹ in Lakhs)', fontsize=11, fontweight='600')
    plt.legend(frameon=True)
    plt.tight_layout()
    p4 = os.path.join(PLOTS_DIR, 'profit_analysis.png')
    plt.savefig(p4)
    plt.close()
    print(f" Saved: {p4}")

    # 5. City-wise Sales Distribution
    plt.figure(figsize=(11, 5), dpi=300)
    city_sales = df.groupby('customer_city')['total_sales_amount'].sum().sort_values(ascending=False).head(10) / 1e5
    sns.barplot(x=city_sales.index, y=city_sales.values, palette='Blues_r')
    plt.title('Top 10 Cities by Total Sales (₹ in Lakhs)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('City', fontsize=11, fontweight='600')
    plt.ylabel('Sales (₹ in Lakhs)', fontsize=11, fontweight='600')
    plt.xticks(rotation=30)
    plt.tight_layout()
    p5 = os.path.join(PLOTS_DIR, 'city_sales.png')
    plt.savefig(p5)
    plt.close()
    print(f" Saved: {p5}")

    # 6. Sales Growth Analysis (MoM)
    plt.figure(figsize=(12, 5), dpi=300)
    monthly_series = df.groupby('year_month')['total_sales_amount'].sum()
    mom_growth = monthly_series.pct_change() * 100
    growth_colors = ['#10b981' if val >= 0 else '#ef4444' for val in mom_growth.fillna(0)]
    plt.bar(mom_growth.index.astype(str), mom_growth.fillna(0), color=growth_colors, width=0.6)
    plt.axhline(0, color='#64748b', linewidth=1)
    plt.title('Month-over-Month Sales Growth (%)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=11, fontweight='600')
    plt.ylabel('Growth Percentage (%)', fontsize=11, fontweight='600')
    plt.xticks(rotation=45)
    plt.tight_layout()
    p6 = os.path.join(PLOTS_DIR, 'sales_growth.png')
    plt.savefig(p6)
    plt.close()
    print(f" Saved: {p6}")

    print("All EDA visualizations successfully constructed and saved to static_plots/.")

if __name__ == '__main__':
    df = load_data()
    run_data_audit(df)
    generate_eda_visualizations(df)
