from django.db import models

# shop model
class Shop(models.Model):
    names = models.CharField(
        max_length=255,
        verbose_name="Shop Name",
        help_text="The full name of the shop, e.g., 'Duka la coed ngongona'"
    )
    abbrev = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Abbreviation",
        help_text="A short, unique abbreviation for the shop, e.g., 'CIVE'"
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Comments",
        help_text="Any additional notes about the shop"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="The date and time when this shop was created"
    )

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"
        ordering = ['names']

    def __str__(self):
        return self.abbrev

# shop item model
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255, verbose_name="Product Name")
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Price")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    is_hidden = models.BooleanField(default=False, verbose_name="Temporarily Unavailable")
    is_deleted = models.BooleanField(default=False, verbose_name="Deleted")
    expiry_date = models.DateField(null=True, blank=True, default=None, verbose_name="Expiry Date")
    comment = models.TextField(null=True, blank=True, default=None, verbose_name="Additional Notes")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


# Cart model
class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT, related_name='cart_users')

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ['-qty']
    
    def __str__(self):
        return str(self.product)
    

# Sales model
class Sales(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT, related_name='sales_user')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shop_sale')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale amount")
    customer = models.CharField(max_length=255, default='n/a', verbose_name="Customer name")
    comment = models.TextField(null=True, blank=True, default=None)
    
    def __str__(self):
        return str(self.amount)


# Sales_items model
class Sale_items(models.Model):
    id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='sales')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sale_product')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Item price")
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Item qty")
    
    def __str__(self):
        return str(self.product)

