from django.contrib import admin
from .models import Address, Qualification, Skill, Contract, Invoice, Payment, Notification, Profession


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['city', 'country', 'street_address', 'postal_code']
    list_filter = ['country', 'city']
    search_fields = ['city', 'country', 'street_address']


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_type', 'get_client', 'status', 'effective_date', 'expiry_date']
    list_filter = ['contract_type', 'status']
    search_fields = ['template_version']
    date_hierarchy = 'effective_date'

    def get_client(self, obj):
        """Display the client for this contract"""
        if obj.employer_profile:
            return f"Employer: {obj.employer_profile.company_name}"
        elif obj.eor_client_profile:
            return f"EOR Client: {obj.eor_client_profile.company_name}"
        return "No client assigned"
    get_client.short_description = 'Client'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'get_client', 'get_total_amount', 'status', 'issue_date', 'due_date']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number']
    date_hierarchy = 'issue_date'

    def get_client(self, obj):
        """Display the client for this invoice"""
        return str(obj.client)
    get_client.short_description = 'Client'

    def get_total_amount(self, obj):
        """Display the total amount for this invoice"""
        return f"€{obj.total_amount:.2f}"
    get_total_amount.short_description = 'Total Amount'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount_paid', 'payment_date', 'method', 'status']
    list_filter = ['method', 'status', 'payment_date']
    search_fields = ['transaction_id', 'invoice__invoice_number']
    date_hierarchy = 'payment_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__email', 'message']
    date_hierarchy = 'created_at'


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']