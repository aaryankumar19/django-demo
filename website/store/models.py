from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Category(models.Model):
    name = models.CharField(max_length=1000, unique=True)
    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    google_file_id = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    original_price = models.PositiveIntegerField()
    discounted_price = models.PositiveIntegerField()

    UNIT_CHOICES = [
        ("g", "Grams"),
        ("ml", "Milliliters"),
        ("pcs", "Pieces"),
        ("kg", "Kilograms"),
        ("ltr", "Liters"),
    ]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="g")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    stock = models.PositiveBigIntegerField(default=0)

    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    google_file_id = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def discount_percentage(self):
        if self.original_price > 0:
            return round(((self.original_price - self.discounted_price) / self.original_price) * 100, 2)
        return 0

    def clean(self):
        if self.discounted_price and self.original_price:
            if self.discounted_price > self.original_price:
                raise ValidationError("Discounted price cannot be greater than original price.")

    def __str__(self):
        return self.name


class Banner(models.Model):
    BANNER_TYPES = [
        ("category", "Category"),
        ("product", "Product"),
    ]

    title = models.CharField(max_length=100)
    text = models.CharField(max_length=50, blank=False, null=False)
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPES)

    image_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    google_file_id = models.CharField(max_length=255, blank=True, default="")

    search_query = models.CharField(max_length=2000)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title