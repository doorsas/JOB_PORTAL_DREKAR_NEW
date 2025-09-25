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
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
        ('NO_SHOW', 'No Show'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='work_schedules')
    assignment = models.ForeignKey(
        'employers.Assignment',
        on_delete=models.CASCADE,
        related_name='work_schedules',
        null=True,
        blank=True
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')

    # Additional fields
    location = models.CharField(max_length=255, blank=True, null=True)
    job_position = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_schedules'
    )

    class Meta:
        unique_together = ['employee', 'assignment', 'date', 'start_time']
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.employee.full_name} - {self.assignment.employer.company_name} - {self.date}"

    @property
    def total_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        total_time = end - start - timedelta(minutes=self.break_duration_minutes)
        return total_time.total_seconds() / 3600

    @property
    def employer(self):
        """Get the employer from assignment"""
        return self.assignment.employer if self.assignment else None


class Timesheet(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RESUBMIT', 'Needs Resubmission'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='timesheets')
    work_schedule = models.OneToOneField(WorkSchedule, on_delete=models.CASCADE, related_name='timesheet', null=True, blank=True)
    assignment = models.ForeignKey('employers.Assignment', on_delete=models.CASCADE, related_name='timesheets', null=True, blank=True)

    # Time tracking
    date = models.DateField()
    actual_start_time = models.TimeField(blank=True, null=True)
    actual_end_time = models.TimeField(blank=True, null=True)
    break_duration = models.IntegerField(default=0, help_text="Break duration in minutes")
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='approved_timesheets'
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['employee', 'assignment', 'date']
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Auto-populate assignment from work_schedule
        if self.work_schedule and not hasattr(self, 'assignment') or not self.assignment:
            self.assignment = self.work_schedule.assignment
        if self.work_schedule and not self.date:
            self.date = self.work_schedule.date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.hours_worked}h)"

    @property
    def total_hours(self):
        return self.hours_worked + self.overtime_hours

    @property
    def employer(self):
        return self.assignment.employer if self.assignment else None


class Payslip(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent to Employee'),
        ('VIEWED', 'Viewed by Employee'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='payslips')
    assignment = models.ForeignKey(
        'employers.Assignment',
        on_delete=models.CASCADE,
        related_name='payslips',
        null=True,
        blank=True
    )

    # Period information
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    pay_date = models.DateField(null=True, blank=True)

    # Financial details
    base_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Detailed breakdown
    deductions_json = models.JSONField(default=dict)
    bonuses_json = models.JSONField(default=dict)

    # File and status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    file = models.FileField(upload_to='payslips/%Y/%m/', blank=True, null=True)
    issue_date = models.DateField()
    viewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['employee', 'assignment', 'period_start_date', 'period_end_date']
        ordering = ['-period_start_date']

    def __str__(self):
        return f"Payslip for {self.employee.full_name} - {self.assignment.employer.company_name} ({self.period_start_date} - {self.period_end_date})"

    @property
    def employer(self):
        return self.assignment.employer


class CV(models.Model):
    """
    Employee CV with additional details.
    """
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, related_name='cv')
    education = models.TextField(verbose_name="Education", help_text="Describe your educational background")
    experience = models.TextField(verbose_name="Work Experience", help_text="Describe your work experience")
    skills = models.TextField(verbose_name="Skills", help_text="List your professional skills")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    place_of_birth = models.CharField(max_length=255, blank=True, verbose_name="Place of Birth")
    place_of_residence = models.CharField(max_length=255, blank=True, verbose_name="Place of Residence")
    contacts = models.CharField(max_length=255, blank=True, verbose_name="Emergency Contacts")
    languages = models.TextField(blank=True, verbose_name="Languages", help_text="Languages you speak and proficiency level")
    civil_status = models.CharField(max_length=100, blank=True, verbose_name="Civil Status")
    professional_experience = models.TextField(blank=True, verbose_name="Professional Experience", help_text="Detailed professional experience")
    other_relevant_information = models.TextField(blank=True, verbose_name="Other Relevant Information")
    characteristics = models.TextField(blank=True, verbose_name="Personal Characteristics")
    hobby = models.TextField(blank=True, verbose_name="Hobbies & Interests")
    attachment = models.FileField(upload_to='cv_attachments/', blank=True, null=True, verbose_name="CV Attachment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "CVs"

    def __str__(self):
        return f"CV of {self.employee.full_name}"

    @property
    def is_complete(self):
        """Check if CV has minimum required information"""
        required_fields = [self.education, self.experience, self.skills]
        return all(field.strip() for field in required_fields if field)