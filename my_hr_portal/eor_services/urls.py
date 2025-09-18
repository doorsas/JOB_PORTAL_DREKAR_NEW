from django.urls import path
from . import views

app_name = 'eor_services'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
]