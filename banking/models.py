from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("savings", "Savings Account"),
        ("current", "Current Account"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    account_number = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    bvn = models.CharField(max_length=11)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default="current")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("1000000000.00"))
    transaction_pin = models.CharField(max_length=128, blank=True, default="")

    def __str__(self):
        return f"{self.full_name} ({self.account_number})"
