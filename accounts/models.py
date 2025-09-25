from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CUSTOMER = "customer"
    ROLE_SELLER = "seller"
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, "Customer"),
        (ROLE_SELLER, "Seller"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)

    def __str__(self):
        return f"{self.username} ({self.role})"
