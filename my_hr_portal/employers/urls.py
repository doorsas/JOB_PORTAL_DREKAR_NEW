from django.urls import path
from . import views

app_name = 'employers'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('jobs/', views.job_postings_list, name='job_postings_list'),
    path('jobs/create/', views.create_job_posting, name='create_job_posting'),
    path('jobs/<int:job_id>/', views.job_posting_detail, name='job_posting_detail'),
    path('jobs/<int:job_id>/edit/', views.edit_job_posting, name='edit_job_posting'),
    path('jobs/<int:job_id>/delete/', views.delete_job_posting, name='delete_job_posting'),
    path('jobs/<int:job_id>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:application_id>/', views.application_detail, name='application_detail'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
]