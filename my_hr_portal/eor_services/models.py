from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from core.models import BaseClientProfile,Contract

class EORClientProfile(BaseClientProfile):
    pass

    def __str__(self):
        return self.company_name


class EORAgreement(TimeStampedModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_SIGNATURE', 'Pending Signature'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
    ]

    eor_client = models.ForeignKey(EORClientProfile, on_delete=models.CASCADE, related_name='eor_agreements')
    agreement_type = models.CharField(max_length=50)
    terms_and_conditions = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    signed_document = models.FileField(upload_to='eor_agreements/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    def __str__(self):
        return f"EOR Agreement - {self.eor_client.company_name} ({self.status})"


class EORPlacement(TimeStampedModel):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
    ]

    eor_client = models.ForeignKey(EORClientProfile, on_delete=models.CASCADE, related_name='eor_placements')
    employee = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='eor_placements')
    eor_agreement = models.ForeignKey(EORAgreement, on_delete=models.CASCADE, related_name='placements')
    job_title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    employment_contract = models.OneToOneField('core.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='eor_placement')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.employee.full_name} at {self.eor_client.company_name} ({self.job_title})"


class PayrollRun(TimeStampedModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PROCESSED', 'Processed'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    eor_client = models.ForeignKey(EORClientProfile, on_delete=models.CASCADE, related_name='payroll_runs')
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    run_date = models.DateTimeField(auto_now_add=True)
    total_gross_payout = models.DecimalField(max_digits=12, decimal_places=2)
    total_net_payout = models.DecimalField(max_digits=12, decimal_places=2)
    total_taxes = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    xml_export_file = models.FileField(upload_to='payroll_exports/', blank=True, null=True)
    generated_payslips = models.ManyToManyField('employees.Payslip', blank=True, related_name='payroll_runs')

    class Meta:
        unique_together = ['eor_client', 'period_start_date', 'period_end_date']

    def __str__(self):
        return f"Payroll Run for {self.eor_client.company_name} ({self.period_start_date} - {self.period_end_date})"