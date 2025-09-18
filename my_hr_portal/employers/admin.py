from django.contrib import admin
from .models import EmployerProfile, JobPosting, Application, Assignment


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person_name', 'phone', 'internal_verification_status']
    list_filter = ['internal_verification_status']
    search_fields = ['company_name', 'registration_code', 'contact_person_name', 'contact_person_email']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'job_type', 'status', 'created_at', 'closing_date']
    list_filter = ['job_type', 'status', 'created_at']
    search_fields = ['title', 'description', 'employer__company_name']
    filter_horizontal = ['required_qualifications', 'required_skills']
    date_hierarchy = 'created_at'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job_posting', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'job_posting__title']
    date_hierarchy = 'created_at'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'employer', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'employer__company_name']
    date_hierarchy = 'start_date'