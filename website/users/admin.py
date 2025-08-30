from django.contrib import admin
from .models import Address, CartItem, WishlistItem


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'phone_number', 'city', 'pincode', 'created_at')
    search_fields = ('full_name', 'phone_number', 'city', 'pincode', 'user__email', 'user__username')
    list_filter = ('city', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'subtotal', 'added_at')
    search_fields = ('user__email', 'user__username', 'product__name')
    list_filter = ('added_at',)
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
    list_per_page = 20

    def subtotal(self, obj):
        return obj.subtotal()
    subtotal.short_description = 'Subtotal'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'added_at')
    search_fields = ('user__email', 'user__username', 'product__name')
    list_filter = ('added_at',)
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
    list_per_page = 20
