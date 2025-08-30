from django.contrib import admin
from .models import User, OTPRequest


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user_token", "created_at")
    search_fields = ("phone_number", "user_token")
    list_filter = ("created_at",)
    readonly_fields = ("user_token", "created_at")
    ordering = ("-created_at",)


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "otp", "created_at")
    search_fields = ("phone_number", "otp")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
