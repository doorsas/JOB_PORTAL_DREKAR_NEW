from django.contrib import admin
from .models import EmployerProfile, JobPosting, Application, Assignment


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person_name', 'phone', 'internal_verification_status']
    list_filter = ['internal_verification_status']
    search_fields = ['company_name', 'registration_code', 'contact_person_name', 'contact_person_email']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'job_type', 'status', 'posted_date', 'closing_date']
    list_filter = ['job_type', 'status', 'posted_date']
    search_fields = ['title', 'description', 'employer__company_name']
    filter_horizontal = ['required_qualifications', 'required_skills']
    date_hierarchy = 'posted_date'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job_posting', 'status', 'application_date']
    list_filter = ['status', 'application_date']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'job_posting__title']
    date_hierarchy = 'application_date'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'employer', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'employer__company_name']
    date_hierarchy = 'start_date'