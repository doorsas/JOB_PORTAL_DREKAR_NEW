# employees/services.py
from django.db.models import Sum
from datetime import date
from .models import Timesheet, Payslip
# Assume you have a PDF generation utility like in the invoice example
from core.utils import generate_payslip_pdf 

def calculate_taxes_and_deductions(gross_salary):
    # THIS IS A PLACEHOLDER. Real tax logic is extremely complex.
    tax_amount = gross_salary * 0.20 # Simplified 20% tax
    other_deductions = 50.00 # e.g., for insurance
    deductions_json = {'tax': float(tax_amount), 'insurance': other_deductions}
    net_salary = gross_salary - tax_amount - other_deductions
    return net_salary, tax_amount, deductions_json

def generate_payslip_for_employee(employee_profile, period_start, period_end):
    # 1. Gather all approved timesheets in the period
    approved_timesheets = Timesheet.objects.filter(
        employee=employee_profile,
        status='APPROVED',
        date__range=(period_start, period_end)
    )

    if not approved_timesheets:
        return None # No work, no payslip

    # 2. Calculate total hours
    total_hours_data = approved_timesheets.aggregate(
        total_regular=Sum('hours_worked'),
        total_overtime=Sum('overtime_hours')
    )
    total_regular = total_hours_data['total_regular'] or 0
    total_overtime = total_hours_data['total_overtime'] or 0

    # 3. Determine pay rates (this should come from the contract or assignment)
    REGULAR_RATE = 20.00 # Placeholder
    OVERTIME_RATE = 30.00 # Placeholder

    # 4. Calculate Gross Salary
    gross_salary = (total_regular * REGULAR_RATE) + (total_overtime * OVERTIME_RATE)

    # 5. Calculate Net Salary
    net_salary, tax_amount, deductions_json = calculate_taxes_and_deductions(gross_salary)

    # 6. Create the Payslip object
    payslip = Payslip.objects.create(
        employee=employee_profile,
        period_start_date=period_start,
        period_end_date=period_end,
        issue_date=date.today(),
        gross_salary=gross_salary,
        net_salary=net_salary,
        tax_amount=tax_amount,
        deductions_json=deductions_json
    )

    # 7. Generate and attach the PDF
    # pdf_in_memory = generate_payslip_pdf(payslip)
    # file_name = f'Payslip-{payslip.employee}-{payslip.period_start_date}.pdf'
    # payslip.file.save(file_name, ContentFile(pdf_in_memory.getvalue()))
    
    print(f"Generated payslip {payslip.id} for {employee_profile}")
    return payslip