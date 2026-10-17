from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, primary_key=True, db_column='customer_id')
    customer_name = models.CharField(max_length=150)
    customer_city = models.CharField(max_length=100)
    customer_state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'
        managed = True
        ordering = ['customer_name']

    def __str__(self):
        return f"{self.customer_name} ({self.customer_city})"

class Product(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True, db_column='product_id')
    product_name = models.CharField(max_length=255)
    product_category = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        managed = True
        ordering = ['product_name']

    def __str__(self):
        return f"{self.product_name} [{self.product_category}]"

class SalesTransaction(models.Model):
    sale_id = models.CharField(max_length=50, primary_key=True, db_column='sale_id')
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column='customer_id')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, db_column='product_id')
    product_name = models.CharField(max_length=255)
    product_category = models.CharField(max_length=100)
    sale_date = models.DateField()
    quantity_sold = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    total_sales_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    customer_city = models.CharField(max_length=100)
    customer_state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_transactions'
        managed = True
        ordering = ['-sale_date', '-sale_id']

    def __str__(self):
        return f"{self.sale_id} - {self.product_name} (Rs. {self.total_sales_amount})"
