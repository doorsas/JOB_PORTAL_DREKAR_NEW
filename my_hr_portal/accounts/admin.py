from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'user_type', 'is_verified', 'is_staff', 'is_active', 'registration_date']
    list_filter = ['user_type', 'is_verified', 'is_staff', 'is_active', 'registration_date']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-registration_date']
    readonly_fields = ['registration_date']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'is_verified', 'registration_date')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('email', 'user_type', 'is_verified')
        }),
    )