from django.db import models


class Crips(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, verbose_name="Crips type")
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    comment = models.TextField(null=True, blank=True, default=None, verbose_name="Additional Notes")

    def __str__(self):
        return f"{self.name}"
