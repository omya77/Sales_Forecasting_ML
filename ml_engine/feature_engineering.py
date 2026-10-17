"""
Feature Engineering Module for Sales Forecasting
Extracts temporal, cyclical, lag, and rolling statistics from historical sales.
"""

import pandas as pd
import numpy as np

def prepare_daily_sales_features(df):
    """
    Aggregates transactional sales into daily time-series and engineers features:
    - Date calendar indicators (year, month, day, dayofweek, quarter, weekend, festive)
    - Lag features (sales from 1, 2, 7, 14, 30 days ago)
    - Moving average & volatility statistics (7-day and 30-day rolling means and standard deviations)
    """
    df_clean = df.copy()
    if 'sale_date' in df_clean.columns:
        df_clean['sale_date'] = pd.to_datetime(df_clean['sale_date'])
    
    # Daily aggregation
    daily = df_clean.groupby('sale_date').agg(
        total_sales=('total_sales_amount', 'sum'),
        total_profit=('profit', 'sum'),
        total_transactions=('sale_id', 'count'),
        total_quantity=('quantity_sold', 'sum'),
        avg_discount=('discount', 'mean')
    ).reset_index()
    
    daily = daily.sort_values('sale_date').set_index('sale_date')
    
    # Reindex to ensure continuous daily date range
    full_idx = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq='D')
    daily = daily.reindex(full_idx)
    
    # Fill any missing days with 0 sales or forward fill
    daily['total_sales'] = daily['total_sales'].fillna(0.0)
    daily['total_profit'] = daily['total_profit'].fillna(0.0)
    daily['total_transactions'] = daily['total_transactions'].fillna(0)
    daily['total_quantity'] = daily['total_quantity'].fillna(0)
    daily['avg_discount'] = daily['avg_discount'].fillna(0.0)
    
    # Calendar Features
    daily['year'] = daily.index.year
    daily['month'] = daily.index.month
    daily['day'] = daily.index.day
    daily['dayofweek'] = daily.index.dayofweek
    daily['quarter'] = daily.index.quarter
    daily['is_weekend'] = daily['dayofweek'].isin([5, 6]).astype(int)
    daily['is_month_start'] = daily.index.is_month_start.astype(int)
    daily['is_month_end'] = daily.index.is_month_end.astype(int)
    
    # Festive Season Indicator (India festive quarter: Oct, Nov, Dec)
    daily['is_festive'] = daily['month'].isin([10, 11, 12]).astype(int)
    
    # Lag Features (Past actual sales)
    daily['lag_1'] = daily['total_sales'].shift(1)
    daily['lag_2'] = daily['total_sales'].shift(2)
    daily['lag_7'] = daily['total_sales'].shift(7)
    daily['lag_14'] = daily['total_sales'].shift(14)
    daily['lag_30'] = daily['total_sales'].shift(30)
    
    # Rolling Window Features (Capturing medium and long term momentum)
    daily['rolling_mean_7'] = daily['total_sales'].shift(1).rolling(window=7).mean()
    daily['rolling_std_7'] = daily['total_sales'].shift(1).rolling(window=7).std()
    daily['rolling_mean_30'] = daily['total_sales'].shift(1).rolling(window=30).mean()
    daily['rolling_std_30'] = daily['total_sales'].shift(1).rolling(window=30).std()
    
    # Drop warm-up rows (first 30 days due to lag_30)
    daily_features = daily.dropna().reset_index().rename(columns={'index': 'date'})
    return daily_features

FEATURE_COLUMNS = [
    'year', 'month', 'day', 'dayofweek', 'quarter', 
    'is_weekend', 'is_month_start', 'is_month_end', 'is_festive',
    'lag_1', 'lag_2', 'lag_7', 'lag_14', 'lag_30',
    'rolling_mean_7', 'rolling_std_7', 'rolling_mean_30', 'rolling_std_30'
]
TARGET_COLUMN = 'total_sales'
