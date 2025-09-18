from django.contrib import admin
from .models import EmployeeProfile, WorkSchedule, Timesheet, Payslip


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'nationality', 'current_status', 'expected_salary']
    list_filter = ['current_status', 'nationality']
    search_fields = ['first_name', 'last_name', 'user__email']
    filter_horizontal = ['preferred_professions', 'skills']


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'start_time', 'end_time', 'status', 'total_hours']
    list_filter = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']
    date_hierarchy = 'date'


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'hours_worked', 'overtime_hours', 'status', 'approved_by']
    list_filter = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']
    date_hierarchy = 'date'


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee', 'period_start_date', 'period_end_date', 'gross_salary', 'net_salary', 'issue_date']
    list_filter = ['issue_date']
    search_fields = ['employee__first_name', 'employee__last_name']
    date_hierarchy = 'issue_date'