from django.db import models
from authentication.models import User
from store.models import Product
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# Create your models here.

phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message="Enter a valid phone number.")],
        help_text="Phone number including country code (optional)."
    )
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'address'
        ordering = ['-created_at']
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        indexes = [
            models.Index(fields=['user'], name='idx_address_user'),
            models.Index(fields=['city'], name='idx_address_city')
        ]

    def clean(self):
        # Enforce max 5 addresses per user
        if self.user.addresses.count() >= 5 and not self.pk:  # only for new records
            raise ValidationError("You can only add up to 5 addresses per account.")

    def __str__(self):
        return f"{self.full_name}, {self.city}"
    

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def subtotal(self):
        return self.product.discounted_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Cart of {self.user})"

class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.product.name} in {self.user}'s wishlist"


