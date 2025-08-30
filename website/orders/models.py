from django.db import models
from authentication.models import User
from users.models import Address, CartItem
from store.models import Product, Category


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)   # e.g. "Cash on Delivery"
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # extra fee if any
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return f"{self.name} ({'Enabled' if self.is_enabled else 'Disabled'})"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.TextField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    payment_method = models.ForeignKey("orders.PaymentMethod", on_delete=models.PROTECT, related_name="orders")

    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_totals(self):
        subtotal = sum(item.subtotal() for item in self.items.all())
        self.subtotal_price = subtotal
        total = subtotal + self.delivery_price - self.discount
        if total < 0:
            total = 0
        self.total_price = total
        self.save()
        return total

    def __str__(self):
        return f"Order #{self.id} by {self.user} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"
