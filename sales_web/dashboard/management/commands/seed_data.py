"""
Django Management Command: seed_data
Populates customers, products, and sales transactions from dataset/sales_data.csv
and provisions a default administrative superuser for production deployment.
"""

import os
import csv
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from dashboard.models import Customer, Product, SalesTransaction


class Command(BaseCommand):
    help = "Seeds initial sales dataset and default superuser if database is empty."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Checking database initialization state..."))

        # 1. Provision Default Admin User if none exists
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            admin_pass = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")
            admin_email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@salesforecast.ai")

            self.stdout.write(f"Creating default superuser '{admin_user}'...")
            User.objects.create_superuser(username=admin_user, email=admin_email, password=admin_pass)
            self.stdout.write(self.style.SUCCESS(f"Default admin user '{admin_user}' created successfully!"))
        else:
            self.stdout.write("Superuser already exists. Skipping user creation.")

        # 2. Check if transactions already exist
        tx_count = SalesTransaction.objects.count()
        if tx_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Database already contains {tx_count:,} transactions. Seeding skipped."))
            return

        # 3. Locate CSV file
        csv_candidates = [
            settings.BASE_DIR.parent / "dataset" / "sales_data.csv",
            settings.BASE_DIR / "dataset" / "sales_data.csv",
            settings.BASE_DIR / "sales_data.csv",
        ]
        csv_path = None
        for p in csv_candidates:
            if os.path.exists(p):
                csv_path = p
                break

        if not csv_path:
            self.stdout.write(self.style.WARNING(f"Dataset CSV not found in {csv_candidates}. Skipping transaction seeding."))
            return

        self.stdout.write(f"Reading dataset from {csv_path}...")
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"Found {len(rows):,} rows in dataset. Preparing records...")

        customers_dict = {}
        products_dict = {}
        tx_objects = []

        for r in rows:
            c_id = r["Customer ID"]
            if c_id not in customers_dict:
                customers_dict[c_id] = Customer(
                    customer_id=c_id,
                    customer_name=r["Customer Name"],
                    customer_city=r["Customer City"],
                    customer_state=r["Customer State"]
                )

            p_id = r["Product ID"]
            if p_id not in products_dict:
                products_dict[p_id] = Product(
                    product_id=p_id,
                    product_name=r["Product Name"],
                    product_category=r["Product Category"],
                    unit_price=Decimal(str(r["Unit Price"])),
                    cost_price=Decimal(str(r["Cost Price"]))
                )

        # Bulk create customers
        self.stdout.write(f"Inserting {len(customers_dict):,} unique customers...")
        Customer.objects.bulk_create(list(customers_dict.values()), ignore_conflicts=True)

        # Bulk create products
        self.stdout.write(f"Inserting {len(products_dict):,} unique products...")
        Product.objects.bulk_create(list(products_dict.values()), ignore_conflicts=True)

        # Build transactions
        self.stdout.write("Building transactions list...")
        for r in rows:
            sale_date_val = r.get("Sale Date") or r.get("Date")
            if not sale_date_val:
                continue
            sale_date = datetime.strptime(sale_date_val.strip(), "%Y-%m-%d").date()
            
            sale_id_val = r.get("Sale ID") or r.get("Transaction ID")
            discount_val = r.get("Discount") or r.get("Discount Applied") or 0

            tx_objects.append(SalesTransaction(
                sale_id=sale_id_val,
                customer_id=r["Customer ID"],
                product_id=r["Product ID"],
                product_name=r["Product Name"],
                product_category=r["Product Category"],
                sale_date=sale_date,
                quantity_sold=int(float(r["Quantity Sold"])),
                unit_price=Decimal(str(r["Unit Price"])),
                discount=Decimal(str(discount_val)),
                total_sales_amount=Decimal(str(r["Total Sales Amount"])),
                cost_price=Decimal(str(r.get("Cost Price") or 0)),
                profit=Decimal(str(r.get("Profit") or 0)),
                payment_method=r.get("Payment Method", "UPI"),
                customer_city=r.get("Customer City", "Mumbai"),
                customer_state=r.get("Customer State", "Maharashtra")
            ))

        # Bulk create transactions in batches of 1500
        batch_size = 1500
        total_batches = (len(tx_objects) + batch_size - 1) // batch_size
        self.stdout.write(f"Inserting {len(tx_objects):,} transactions in {total_batches} batches...")

        for i in range(0, len(tx_objects), batch_size):
            chunk = tx_objects[i:i + batch_size]
            SalesTransaction.objects.bulk_create(chunk, ignore_conflicts=True)

        final_count = SalesTransaction.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Seeding completed successfully! Total transactions in DB: {final_count:,}"))
