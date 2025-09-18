from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('EMPLOYER', 'Employer'),
        ('EMPLOYEE', 'Employee'),
        ('EOR_CLIENT', 'EOR Client'),
        ('ADMIN', 'Admin'),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='EMPLOYEE'
    )
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} - {self.get_user_type_display()}"