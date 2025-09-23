from django.contrib import admin
from datetime import date, timedelta
from .models import EmployerProfile, JobPosting, Application, Assignment
from .services import generate_invoice_for_employer

@admin.action(description='Generate monthly invoice for selected employers')
def generate_invoice_action(modeladmin, request, queryset):
    # For simplicity, this bills for the previous month
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_day_previous_month = first_day_current_month - timedelta(days=1)
    first_day_previous_month = last_day_previous_month.replace(day=1)

    for employer in queryset:
        generate_invoice_for_employer(employer, first_day_previous_month, last_day_previous_month)

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person_name', 'phone', 'internal_verification_status', 'has_logo']
    list_filter = ['internal_verification_status']
    search_fields = ['company_name', 'registration_code', 'contact_person_name', 'contact_person_email']
    fields = ['user', 'company_name', 'registration_code', 'address', 'contact_person_name',
              'contact_person_email', 'contact_person_phone', 'phone', 'website', 'logo',
              'internal_verification_status', 'verification_notes']
    actions = [generate_invoice_action]

    def has_logo(self, obj):
        return bool(obj.logo)
    has_logo.boolean = True
    has_logo.short_description = 'Logo'


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'job_type', 'status', 'created_at', 'closing_date']
    list_filter = ['job_type', 'status', 'created_at']
    search_fields = ['title', 'description', 'employer__company_name']
    filter_horizontal = ['required_qualifications', 'required_skills']
    date_hierarchy = 'created_at'
    list_select_related = ('employer', 'location')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job_posting', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'job_posting__title']
    date_hierarchy = 'created_at'
    list_select_related = ('job_posting', 'applicant', 'job_posting__employer')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'employer', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'employer__company_name']
    date_hierarchy = 'start_date'
    list_select_related = ('employee', 'employer', 'job_posting')