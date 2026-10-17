"""
Setup MySQL Database and Populate Historical Data from CSV
Executes database creation, table creation, and bulk insertion.
"""

import os
import csv
import pymysql
from db_connection import get_server_connection, DB_CONFIG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "dataset", "sales_data.csv")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

def setup_database():
    print(f"Connecting to MySQL server at {DB_CONFIG['host']}:{DB_CONFIG['port']} as '{DB_CONFIG['user']}'...")
    conn = get_server_connection()
    cursor = conn.cursor()
    
    try:
        # Create database
        db_name = DB_CONFIG["database"]
        print(f"Creating database `{db_name}` if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE {db_name};")
        
        # Read and run schema statements
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql_statements = f.read().split(";")
            
        print("Creating tables (customers, products, sales_transactions)...")
        for stmt in sql_statements:
            clean_stmt = stmt.strip()
            if clean_stmt:
                cursor.execute(clean_stmt)
        conn.commit()
        print("Tables initialized successfully.")
        
        # Load and insert data from CSV
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"Sales dataset not found at {CSV_PATH}. Please run generate_dataset.py first.")
            
        print(f"Reading dataset from {CSV_PATH}...")
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        print(f"Loaded {len(rows)} records. Preparing unique customers and products...")
        
        customers = {}
        products = {}
        transactions = []
        
        for r in rows:
            # Customers unique map
            c_id = r["Customer ID"]
            if c_id not in customers:
                customers[c_id] = (
                    c_id,
                    r["Customer Name"],
                    r["Customer City"],
                    r["Customer State"]
                )
                
            # Products unique map
            p_id = r["Product ID"]
            if p_id not in products:
                # Estimate single unit cost from cost price / quantity
                qty = float(r["Quantity Sold"]) if float(r["Quantity Sold"]) > 0 else 1.0
                cost_unit = round(float(r["Cost Price"]) / qty, 2)
                products[p_id] = (
                    p_id,
                    r["Product Name"],
                    r["Product Category"],
                    float(r["Unit Price"]),
                    cost_unit
                )
                
            # Transaction row
            transactions.append((
                r["Sale ID"],
                r["Customer ID"],
                r["Product ID"],
                r["Product Name"],
                r["Product Category"],
                r["Sale Date"],
                int(r["Quantity Sold"]),
                float(r["Unit Price"]),
                float(r["Discount"]),
                float(r["Total Sales Amount"]),
                float(r["Cost Price"]),
                float(r["Profit"]),
                r["Payment Method"],
                r["Customer City"],
                r["Customer State"]
            ))
            
        # Bulk Insert Customers
        print(f"Inserting {len(customers)} unique customers...")
        cust_sql = """
            INSERT INTO customers (customer_id, customer_name, customer_city, customer_state)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE customer_name=VALUES(customer_name), customer_city=VALUES(customer_city), customer_state=VALUES(customer_state);
        """
        cursor.executemany(cust_sql, list(customers.values()))
        
        # Bulk Insert Products
        print(f"Inserting {len(products)} unique products...")
        prod_sql = """
            INSERT INTO products (product_id, product_name, product_category, unit_price, cost_price)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE unit_price=VALUES(unit_price), cost_price=VALUES(cost_price);
        """
        cursor.executemany(prod_sql, list(products.values()))
        
        # Bulk Insert Transactions
        print(f"Inserting {len(transactions)} sales transactions...")
        tx_sql = """
            INSERT INTO sales_transactions (
                sale_id, customer_id, product_id, product_name, product_category,
                sale_date, quantity_sold, unit_price, discount, total_sales_amount,
                cost_price, profit, payment_method, customer_city, customer_state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE total_sales_amount=VALUES(total_sales_amount);
        """
        cursor.executemany(tx_sql, transactions)
        
        conn.commit()
        print("Database commit successful!")
        
        # Verification counts
        cursor.execute("SELECT COUNT(*) AS total_cust FROM customers;")
        total_cust = cursor.fetchone()["total_cust"]
        cursor.execute("SELECT COUNT(*) AS total_prod FROM products;")
        total_prod = cursor.fetchone()["total_prod"]
        cursor.execute("SELECT COUNT(*) AS total_tx, SUM(total_sales_amount) AS revenue, SUM(profit) AS total_profit FROM sales_transactions;")
        stats = cursor.fetchone()
        
        print("\n================ MYSQL DATABASE POPULATION COMPLETE ================")
        print(f"Database Name: {db_name}")
        print(f"Total Customers:    {total_cust}")
        print(f"Total Products:     {total_prod}")
        print(f"Total Transactions: {stats['total_tx']}")
        print(f"Total Revenue:      Rs. {float(stats['revenue']):,.2f}")
        print(f"Total Profit:       Rs. {float(stats['total_profit']):,.2f}")
        print("====================================================================\n")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_database()
