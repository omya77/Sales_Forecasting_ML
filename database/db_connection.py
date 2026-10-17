"""
Database Connection Manager for MySQL & PyMySQL
Provides reusable connection and data extraction helpers.
"""

import os
import pymysql
import pandas as pd

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "root"),
    "database": os.environ.get("MYSQL_DB", "sales_forecasting_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_server_connection():
    """Connect to MySQL Server without specifying database (for initialization)."""
    cfg = DB_CONFIG.copy()
    cfg.pop("database", None)
    return pymysql.connect(**cfg)

def get_db_connection():
    """Connect directly to the sales_forecasting_db database."""
    return pymysql.connect(**DB_CONFIG)

def fetch_sales_dataframe(query="SELECT * FROM sales_transactions ORDER BY sale_date ASC"):
    """Fetches sales data as a pandas DataFrame directly from MySQL."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        df = pd.DataFrame(rows)
        if not df.empty:
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            for col in ['total_sales_amount', 'unit_price', 'discount', 'cost_price', 'profit']:
                if col in df.columns:
                    df[col] = df[col].astype(float)
        return df
    finally:
        conn.close()
