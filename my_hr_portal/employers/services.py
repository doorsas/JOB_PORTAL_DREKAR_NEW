# employers/services.py (a new file in your employers app)
from datetime import date
from django.db.models import Sum
from core.services import create_invoice_for_client
from employees.models import Timesheet # Assuming Timesheet model exists

def generate_invoice_for_employer(employer_profile, billing_period_start, billing_period_end):
    """
    Gathers billable timesheets for an employer and creates an invoice.
    """
    # Find all approved timesheets for this employer's assignments that haven't been invoiced yet
    billable_timesheets = Timesheet.objects.filter(
        assignment__employer=employer_profile,
        status=Timesheet.TimesheetStatus.APPROVED,
        invoiced=False, # You'll need to add an 'invoiced' boolean field to your Timesheet model
        date__range=(billing_period_start, billing_period_end)
    ).values(
        'assignment__employee__first_name', 
        'assignment__employee__last_name',
        'assignment__job_posting__title'
    ).annotate(
        total_hours=Sum('hours_worked')
    )

    if not billable_timesheets:
        print(f"No billable hours for {employer_profile.company_name} in this period.")
        return None

    # Assume a standard hourly rate for now. In a real app, this would come from the assignment or contract.
    HOURLY_RATE = 50.00 

    line_items_data = []
    for item in billable_timesheets:
        description = (f"Work by {item['assignment__employee__first_name']} {item['assignment__employee__last_name']} "
                       f"({item['assignment__job_posting__title']})")
        line_items_data.append({
            'description': description,
            'quantity': item['total_hours'],
            'unit_price': HOURLY_RATE
        })
    
    # Use the core service to create the invoice
    issue_date = date.today()
    due_date = issue_date + timedelta(days=30)
    invoice = create_invoice_for_client(
        client_object=employer_profile,
        issue_date=issue_date,
        due_date=due_date,
        line_items_data=line_items_data
    )

    # Mark the timesheets as invoiced to prevent double-billing
    Timesheet.objects.filter(id__in=billable_timesheets.values_list('id', flat=True)).update(invoiced=True)
    
    return invoice