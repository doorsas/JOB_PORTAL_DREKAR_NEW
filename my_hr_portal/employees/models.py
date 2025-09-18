from django.db import models
from django.conf import settings
from core.models import Skill, Profession, Address
from core.models import TimeStampedModel


class EmployeeProfile(TimeStampedModel):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('EMPLOYED', 'Employed'),
        ('ON_HOLD', 'On Hold'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    address = models.ForeignKey('core.Address', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50)
    preferred_professions = models.ManyToManyField(Profession, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    experience_summary = models.TextField(blank=True, null=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Document(TimeStampedModel):
    class DocumentType(models.TextChoices):
        CV = 'CV', 'Curriculum Vitae'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        ID = 'ID', 'Identification'
        OTHER = 'OTHER', 'Other'

    employee = models.ForeignKey('EmployeeProfile', related_name='documents', on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to='employee_documents/')
    description = models.CharField(max_length=255, blank=True)


class WorkSchedule(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='work_schedules')
    assignment = models.ForeignKey(
        'employers.Assignment',
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='work_schedules'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')

    class Meta:
        unique_together = ['employee', 'date', 'start_time']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.start_time}-{self.end_time})"

    @property
    def total_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        total_time = end - start - timedelta(minutes=self.break_duration_minutes)
        return total_time.total_seconds() / 3600


class Timesheet(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='timesheets')
    work_schedule = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, blank=True, null=True)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='approved_timesheets'
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.hours_worked}h)"

    @property
    def total_hours(self):
        return self.hours_worked + self.overtime_hours


class Payslip(TimeStampedModel):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='payslips')
    assignment = models.ForeignKey(
        'employers.Assignment',
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='payslips'
    )
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deductions_json = models.JSONField(default=dict)  # Detailed breakdown of deductions
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    file = models.FileField(upload_to='payslips/', blank=True, null=True)
    issue_date = models.DateField()

    class Meta:
        unique_together = ['employee', 'period_start_date', 'period_end_date']

    def __str__(self):
        return f"Payslip for {self.employee.full_name} ({self.period_start_date} - {self.period_end_date})"