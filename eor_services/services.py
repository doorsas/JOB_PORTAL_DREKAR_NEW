# eor_services/services.py (a new file in your eor_services app)
from datetime import date
from .models import EORPlacement

def generate_invoice_for_eor_client(eor_client_profile, billing_month, billing_year):
    """
    Gathers payroll data for an EOR client and creates an invoice.
    """
    # Find all active placements for this client
    active_placements = EORPlacement.objects.filter(
        eor_client=eor_client_profile,
        status=EORPlacement.PlacementStatus.ACTIVE
    )

    if not active_placements:
        return None

    line_items_data = []
    for placement in active_placements:
        # Line item for the employee's gross salary (this would come from their contract)
        gross_salary = placement.employee.contract.gross_salary # Example relationship
        line_items_data.append({
            'description': f"Gross Salary: {placement.employee}",
            'quantity': 1,
            'unit_price': gross_salary
        })

        # Line item for your management fee (e.g., 10% of salary)
        management_fee = gross_salary * 0.10 
        line_items_data.append({
            'description': f"EOR Service Fee: {placement.employee}",
            'quantity': 1,
            'unit_price': management_fee
        })

    issue_date = date.today()
    due_date = issue_date + timedelta(days=15)
    invoice = create_invoice_for_client(
        client_object=eor_client_profile,
        issue_date=issue_date,
        due_date=due_date,
        line_items_data=line_items_data
    )
    
    return invoice