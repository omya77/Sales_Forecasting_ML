"""
Sales Dataset Generator
Generates realistic historical retail sales transaction data adhering to
all 15 required fields specified in the B.Sc Data Science Project Synopsis.
"""

import os
import random
from datetime import datetime, timedelta

PRODUCTS = [
    # Electronics
    {"id": "PROD-101", "name": "Wireless Bluetooth Earbuds", "category": "Electronics", "unit_price": 1999.0, "cost_price": 1200.0},
    {"id": "PROD-102", "name": "Smart Fitness Watch", "category": "Electronics", "unit_price": 3499.0, "cost_price": 2100.0},
    {"id": "PROD-103", "name": "4K Ultra HD Smart TV 43-inch", "category": "Electronics", "unit_price": 27999.0, "cost_price": 19500.0},
    {"id": "PROD-104", "name": "Fast Charging Power Bank 20000mAh", "category": "Electronics", "unit_price": 1499.0, "cost_price": 850.0},
    {"id": "PROD-105", "name": "Noise Cancelling Headphones", "category": "Electronics", "unit_price": 5999.0, "cost_price": 3800.0},
    {"id": "PROD-106", "name": "Mechanical Gaming Keyboard", "category": "Electronics", "unit_price": 2499.0, "cost_price": 1450.0},
    
    # Fashion & Apparel
    {"id": "PROD-201", "name": "Men's Slim Fit Denim Jeans", "category": "Fashion", "unit_price": 1799.0, "cost_price": 850.0},
    {"id": "PROD-202", "name": "Women's Pure Cotton Kurti", "category": "Fashion", "unit_price": 1299.0, "cost_price": 550.0},
    {"id": "PROD-203", "name": "Breathable Running Sneakers", "category": "Fashion", "unit_price": 2499.0, "cost_price": 1200.0},
    {"id": "PROD-204", "name": "Formal Leather Office Shoes", "category": "Fashion", "unit_price": 3199.0, "cost_price": 1600.0},
    {"id": "PROD-205", "name": "Polarized Aviator Sunglasses", "category": "Fashion", "unit_price": 999.0, "cost_price": 350.0},
    
    # Home & Kitchen
    {"id": "PROD-301", "name": "Stainless Steel Induction Cookware Set", "category": "Home & Kitchen", "unit_price": 3299.0, "cost_price": 1950.0},
    {"id": "PROD-302", "name": "Electric Air Fryer 4.5L", "category": "Home & Kitchen", "unit_price": 4999.0, "cost_price": 3100.0},
    {"id": "PROD-303", "name": "RO Water Purifier 7L", "category": "Home & Kitchen", "unit_price": 8499.0, "cost_price": 5600.0},
    {"id": "PROD-304", "name": "Microfiber Bedsheet King Size", "category": "Home & Kitchen", "unit_price": 1199.0, "cost_price": 520.0},
    {"id": "PROD-305", "name": "Robotic Vacuum Cleaner", "category": "Home & Kitchen", "unit_price": 18999.0, "cost_price": 12800.0},
    
    # Groceries & Essentials
    {"id": "PROD-401", "name": "Organic Basmati Rice 5kg", "category": "Groceries", "unit_price": 650.0, "cost_price": 480.0},
    {"id": "PROD-402", "name": "Cold Pressed Mustard Oil 2L", "category": "Groceries", "unit_price": 420.0, "cost_price": 310.0},
    {"id": "PROD-403", "name": "California Whole Almonds 1kg", "category": "Groceries", "unit_price": 890.0, "cost_price": 680.0},
    {"id": "PROD-404", "name": "Assorted Green Tea 100 Bags", "category": "Groceries", "unit_price": 499.0, "cost_price": 290.0},
    
    # Beauty & Personal Care
    {"id": "PROD-501", "name": "Vitamin C Radiance Face Serum", "category": "Beauty", "unit_price": 699.0, "cost_price": 260.0},
    {"id": "PROD-502", "name": "Anti-Dandruff Herbal Shampoo 500ml", "category": "Beauty", "unit_price": 449.0, "cost_price": 190.0},
    {"id": "PROD-503", "name": "Ultra-Hydrating Moisturizer Cream", "category": "Beauty", "unit_price": 549.0, "cost_price": 210.0},
    
    # Sports & Fitness
    {"id": "PROD-601", "name": "Adjustable Dumbbell Set 20kg", "category": "Sports", "unit_price": 3899.0, "cost_price": 2200.0},
    {"id": "PROD-602", "name": "Anti-Slip TPE Yoga Mat 6mm", "category": "Sports", "unit_price": 899.0, "cost_price": 380.0},
    {"id": "PROD-603", "name": "Whey Protein Powder Isolate 1kg", "category": "Sports", "unit_price": 2699.0, "cost_price": 1750.0},
]

LOCATIONS = [
    {"city": "Mumbai", "state": "Maharashtra"},
    {"city": "Pune", "state": "Maharashtra"},
    {"city": "Nagpur", "state": "Maharashtra"},
    {"city": "Bengaluru", "state": "Karnataka"},
    {"city": "Hyderabad", "state": "Telangana"},
    {"city": "Delhi", "state": "Delhi"},
    {"city": "Ahmedabad", "state": "Gujarat"},
    {"city": "Surat", "state": "Gujarat"},
    {"city": "Chennai", "state": "Tamil Nadu"},
    {"city": "Kolkata", "state": "West Bengal"},
    {"city": "Jaipur", "state": "Rajasthan"},
    {"city": "Indore", "state": "Madhya Pradesh"},
    {"city": "Lucknow", "state": "Uttar Pradesh"},
    {"city": "Chandigarh", "state": "Punjab"},
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]

def generate_customers(num_customers=500):
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
                   "Ananya", "Diya", "Saanvi", "Aadhya", "Pari", "Chiara", "Myra", "Riya", "Avani", "Navya",
                   "Omkar", "Pranav", "Sneha", "Pooja", "Rahul", "Rohit", "Neha", "Priya", "Amit", "Vikram"]
    last_names = ["Sharma", "Verma", "Patil", "Deshmukh", "Kulkarni", "Joshi", "Mehta", "Shah", "Gupta", "Singh",
                  "Reddy", "Nair", "Iyer", "Banerjee", "Chatterjee", "Chopra", "Malhotra", "Yadav", "Patel", "Rao"]
    
    customers = []
    for i in range(1, num_customers + 1):
        c_id = f"CUST-{1000 + i}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        loc = random.choice(LOCATIONS)
        customers.append({
            "customer_id": c_id,
            "name": name,
            "city": loc["city"],
            "state": loc["state"]
        })
    return customers

def generate_sales_data(target_records=6000, start_date=None, end_date=None):
    random.seed(42)
    if start_date is None:
        start_date = datetime(2023, 1, 1)
    if end_date is None:
        end_date = datetime(2025, 12, 31)
        
    days_span = (end_date - start_date).days
    customers = generate_customers(600)
    
    records = []
    
    # We will generate day by day to inject realistic macro trends and seasonality
    current_date = start_date
    sale_counter = 1
    
    while current_date <= end_date:
        month = current_date.month
        day_of_week = current_date.weekday() # 5: Sat, 6: Sun
        
        # Seasonality factors:
        # Festive season boost in Oct-Nov (Diwali/Dussehra)
        # Year-end boost in Dec
        # Summer boost in April-May
        seasonal_mult = 1.0
        if month in [10, 11]:
            seasonal_mult = 1.65
        elif month == 12:
            seasonal_mult = 1.45
        elif month in [4, 5]:
            seasonal_mult = 1.2
        elif month in [7, 8]:
            seasonal_mult = 0.9  # monsoon lull
            
        # Weekend multiplier
        weekend_mult = 1.35 if day_of_week in [5, 6] else 1.0
        
        # Yearly growth trend (e.g., 15% year-over-year)
        year_idx = current_date.year - start_date.year
        growth_mult = 1.0 + (year_idx * 0.18)
        
        # Base daily sales transactions
        base_daily_sales = random.randint(4, 9)
        daily_tx_count = max(2, int(base_daily_sales * seasonal_mult * weekend_mult * growth_mult))
        
        for _ in range(daily_tx_count):
            sale_id = f"SALE-{sale_counter:06d}"
            sale_counter += 1
            
            cust = random.choice(customers)
            prod = random.choice(PRODUCTS)
            
            # Quantity sold usually 1 to 4, higher for Groceries
            if prod["category"] == "Groceries":
                quantity = random.choices([1, 2, 3, 4, 5], weights=[20, 35, 25, 15, 5])[0]
            elif prod["category"] in ["Electronics", "Home & Kitchen"]:
                quantity = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
            else:
                quantity = random.choices([1, 2, 3, 4], weights=[45, 35, 15, 5])[0]
                
            unit_price = prod["unit_price"]
            cost_unit = prod["cost_price"]
            
            # Discounts: 0% to 25%, higher during festive season
            if month in [10, 11, 12]:
                discount_pct = random.choice([5.0, 10.0, 12.0, 15.0, 20.0, 25.0])
            else:
                discount_pct = random.choice([0.0, 0.0, 5.0, 5.0, 10.0, 15.0])
                
            gross_amount = round(quantity * unit_price, 2)
            total_sales_amount = round(gross_amount * (1.0 - discount_pct / 100.0), 2)
            total_cost = round(quantity * cost_unit, 2)
            profit = round(total_sales_amount - total_cost, 2)
            
            # Payment method weights
            payment_method = random.choices(
                PAYMENT_METHODS, 
                weights=[45, 22, 12, 6, 15] # UPI is highest in India
            )[0]
            
            records.append({
                "Sale ID": sale_id,
                "Customer ID": cust["customer_id"],
                "Customer Name": cust["name"],
                "Product ID": prod["id"],
                "Product Name": prod["name"],
                "Product Category": prod["category"],
                "Sale Date": current_date.strftime("%Y-%m-%d"),
                "Quantity Sold": quantity,
                "Unit Price": unit_price,
                "Discount": discount_pct,
                "Total Sales Amount": total_sales_amount,
                "Cost Price": total_cost,
                "Profit": profit,
                "Payment Method": payment_method,
                "Customer City": cust["city"],
                "Customer State": cust["state"]
            })
            
        current_date += timedelta(days=1)
        
    return customers, records

if __name__ == "__main__":
    import csv
    print("Generating comprehensive sales dataset...")
    customers, records = generate_sales_data()
    print(f"Generated {len(records)} sales transactions across {len(customers)} customers.")
    
    out_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(out_dir, "sales_data.csv")
    
    headers = [
        "Sale ID", "Customer ID", "Customer Name", "Product ID", "Product Name", 
        "Product Category", "Sale Date", "Quantity Sold", "Unit Price", "Discount", 
        "Total Sales Amount", "Cost Price", "Profit", "Payment Method", 
        "Customer City", "Customer State"
    ]
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Successfully saved dataset to {csv_file}")
