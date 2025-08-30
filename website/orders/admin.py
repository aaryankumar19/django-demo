# orders/admin.py
from django.contrib import admin
from .models import PaymentMethod, Order, OrderItem


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "charges", "is_enabled")
    list_filter = ("is_enabled",)
    search_fields = ("name",)
    ordering = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "subtotal")  # subtotal works now!
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "payment_method", "total_price", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "user__username", "user__email")
    readonly_fields = ("subtotal_price", "delivery_price", "discount", "total_price", "created_at", "updated_at")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price", "subtotal")
    search_fields = ("order__id", "product__name")
    list_filter = ("order__status", "product")
    ordering = ("-order__created_at",)

