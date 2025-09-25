# tasks.py (in your core app)
from celery import shared_task
from employers.models import EmployerProfile
from employers.services import generate_invoice_for_employer

@shared_task
def run_monthly_billing():
    # ... calculate previous month's date range ...
    billable_employers = EmployerProfile.objects.all() # Or filter for active ones
    for employer in billable_employers:
        generate_invoice_for_employer(employer, start_date, end_date)
    # ... do the same for EOR clients ...