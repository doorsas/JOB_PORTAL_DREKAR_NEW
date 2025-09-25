from django.contrib import admin
from .models import EORClientProfile, EORAgreement, EORPlacement, PayrollRun


@admin.register(EORClientProfile)
class EORClientProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person_name', 'contact_person_email']
    search_fields = ['company_name', 'registration_code', 'contact_person_name']


@admin.register(EORAgreement)
class EORAgreementAdmin(admin.ModelAdmin):
    list_display = ['eor_client', 'agreement_type', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['eor_client__company_name', 'agreement_type']
    date_hierarchy = 'start_date'


@admin.register(EORPlacement)
class EORPlacementAdmin(admin.ModelAdmin):
    list_display = ['employee', 'eor_client', 'job_title', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'eor_client__company_name', 'job_title']
    date_hierarchy = 'start_date'


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ['eor_client', 'period_start_date', 'period_end_date', 'total_gross_payout', 'status', 'run_date']
    list_filter = ['status', 'run_date']
    search_fields = ['eor_client__company_name']
    date_hierarchy = 'run_date'