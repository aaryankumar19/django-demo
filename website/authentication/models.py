import uuid
from django.db import models
from django.core.validators import RegexValidator, MaxLengthValidator, MinLengthValidator
from django.core.exceptions import ValidationError

# Validators
phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")
otp_regex = RegexValidator(regex=r'^\d{6}$', message="OTP must be exactly 6 digits.")

class User(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter a 10-digit phone number."
    )
    user_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['phone_number'], name='idx_user_phone')
        ]

    def __str__(self):
        return self.phone_number


class OTPRequest(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter the phone number associated with the OTP."
    )
    otp = models.CharField(
        max_length=6,
        validators=[otp_regex],
        help_text="6-digit OTP code."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number'], name='idx_otp_phone')
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"
