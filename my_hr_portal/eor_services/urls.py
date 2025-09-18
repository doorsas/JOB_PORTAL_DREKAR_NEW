from django.urls import path
from . import views

app_name = 'eor_services'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]