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
        return self.names

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

