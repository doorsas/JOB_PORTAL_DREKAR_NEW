from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/cv-download/', views.cv_download, name='cv_download'),
    path('cv/', views.cv_view, name='cv_view'),
    path('cv/form/', views.cv_form, name='cv_form'),
    path('documents/', views.document_upload, name='document_upload'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document_delete'),
    path('jobs/', views.job_search, name='job_search'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('applications/', views.my_applications, name='my_applications'),
    path('applications/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('payslips/', views.payslips_view, name='payslips'),
    path('payslips/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('schedules/', views.schedules_view, name='schedules'),
    path('schedules/create/', views.WorkScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<int:schedule_id>/timesheet/', views.submit_timesheet, name='submit_timesheet'),
    path('assignments/', views.my_assignments, name='my_assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
]