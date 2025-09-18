from django.db import models
from django.conf import settings
from core.models import Location, Qualification, Skill, Profession, BaseClientProfile
from core.models import TimeStampedModel


class EmployerProfile(BaseClientProfile):
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    # Additional fields specific to employers (inherited fields: user, company_name, registration_code, address, contact_person_name, contact_person_email)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    contact_person_phone = models.CharField(max_length=20)
    internal_verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='PENDING'
    )
    verification_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.company_name


class JobPosting(TimeStampedModel):
    JOB_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('TEMPORARY', 'Temporary'),
    ]
    
    class JobStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        FILLED = 'FILLED', 'Filled'

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_qualifications = models.ManyToManyField(Qualification, blank=True)
    required_skills = models.ManyToManyField(Skill, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    num_employees_requested = models.IntegerField(default=1)
    estimated_salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    posted_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateField(blank=True, null=True)
    
    
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.DRAFT)
    
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='FULL_TIME')

    def __str__(self):
        return f"{self.title} at {self.employer.company_name}"

    @property
    def is_active(self):
        """Backward compatibility property for checking if job is active"""
        return self.status == 'OPEN'


class Application(TimeStampedModel):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('INVITED', 'Invited'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
        ('RESERVED', 'Reserved'),
    ]

    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='applications')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['job_posting', 'applicant']

    def __str__(self):
        return f"{self.applicant} applied for {self.job_posting.title}"


class Assignment(TimeStampedModel):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('PENDING_START', 'Pending Start'),
        ('TERMINATED', 'Terminated'),
    ]

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='assignments')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_START')
    employment_contract = models.OneToOneField('core.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='assignment')

    def __str__(self):
        return f"{self.employee} assigned to {self.employer.company_name}"