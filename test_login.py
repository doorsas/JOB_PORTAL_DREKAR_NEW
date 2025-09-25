#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_hr_portal.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User

def test_login():
    print("Testing login authentication...")
    print("-" * 50)

    # Get all users
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")

    for user in users:
        print(f"User: {user.username} | Email: {user.email} | Type: {user.user_type}")

        # Test authentication with email (should work)
        auth_result = authenticate(username=user.email, password='admin123')
        if auth_result:
            print(f"[SUCCESS] Email authentication works for {user.email}")
        else:
            print(f"[FAILED] Email authentication failed for {user.email}")

        # Test authentication with username (should fail in our setup)
        auth_result = authenticate(username=user.username, password='admin123')
        if auth_result:
            print(f"[SUCCESS] Username authentication works for {user.username}")
        else:
            print(f"[FAILED] Username authentication failed for {user.username}")

        print("-" * 30)

def test_form_processing():
    print("\nTesting CustomAuthenticationForm...")
    print("-" * 50)

    from accounts.forms import CustomAuthenticationForm
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.post('/accounts/login/')

    # Get a test user
    user = User.objects.first()
    if not user:
        print("No users found to test with")
        return

    # Test form with email
    form_data = {
        'username': user.email,  # Form field is called username but expects email
        'password': 'admin123'
    }

    form = CustomAuthenticationForm(request, data=form_data)
    print(f"Testing form with email: {user.email}")

    if form.is_valid():
        print("[SUCCESS] Form validation works")
        print(f"Authenticated user: {form.get_user()}")
    else:
        print("[FAILED] Form validation failed")
        print(f"Form errors: {form.errors}")

if __name__ == "__main__":
    test_login()
    test_form_processing()