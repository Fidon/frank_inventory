from django.db import models

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

