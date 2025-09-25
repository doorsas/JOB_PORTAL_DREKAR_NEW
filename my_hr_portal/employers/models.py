from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
from core.models import Address, Qualification, Skill, Profession, BaseClientProfile
from core.models import TimeStampedModel


# Optional Celery task for background image processing
# Uncomment the @shared_task decorator if you have Celery configured
# from celery import shared_task

# @shared_task
def resize_employer_logo(employer_profile_id):
    """
    Celery task for resizing employer logos in the background.
    This can be used for batch processing or async image resizing.
    """
    try:
        employer = EmployerProfile.objects.get(id=employer_profile_id)
        if employer.logo:
            # Open the image
            img = Image.open(employer.logo)

            # Check if image needs resizing
            if img.size[0] > 200 or img.size[1] > 200:
                # Resize maintaining aspect ratio
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                # Save to BytesIO buffer
                buffer = BytesIO()
                img_format = img.format if img.format else 'PNG'
                img.save(buffer, format=img_format, quality=85)

                # Replace the image with resized version
                employer.logo.save(
                    employer.logo.name,
                    ContentFile(buffer.getvalue()),
                    save=False
                )
                employer.save()
        return f"Logo resized successfully for {employer.company_name}"
    except EmployerProfile.DoesNotExist:
        return f"EmployerProfile with id {employer_profile_id} not found"
    except Exception as e:
        return f"Error resizing logo: {str(e)}"


class EmployerProfile(BaseClientProfile):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    # Additional fields specific to employers (inherited fields: user, company_name, registration_code, address, contact_person_name, contact_person_email)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    contact_person_phone = models.CharField(max_length=20)
    internal_verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verification_notes = models.TextField(blank=True, null=True)
    logo = models.ImageField(blank=True, null=True, upload_to='employer_logos/', help_text="Company logo (will be resized to 200x200px)")

    def save(self, *args, **kwargs):
        # Resize logo if it exists and is being updated
        if self.logo:
            try:
                # Open the image
                img = Image.open(self.logo)

                # Check if image needs resizing
                if img.size[0] > 200 or img.size[1] > 200:
                    # Resize maintaining aspect ratio
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                    # Save to BytesIO buffer
                    buffer = BytesIO()
                    # Determine format
                    img_format = img.format if img.format else 'PNG'
                    img.save(buffer, format=img_format, quality=85)

                    # Replace the image with resized version
                    self.logo.save(
                        self.logo.name,
                        ContentFile(buffer.getvalue()),
                        save=False
                    )
            except Exception as e:
                # Log error but don't fail the save
                print(f"Error resizing logo: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name


class JobPosting(TimeStampedModel):
    class JobType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        TEMPORARY = 'TEMPORARY', 'Temporary'

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
    location = models.ForeignKey(Address, on_delete=models.CASCADE)
    num_employees_requested = models.IntegerField(default=1)
    estimated_salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    closing_date = models.DateField(blank=True, null=True)
    
    
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.DRAFT)
    
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)

    def __str__(self):
        return f"{self.title} at {self.employer.company_name}"

    @property
    def is_active(self):
        """Backward compatibility property for checking if job is active"""
        return self.status == 'OPEN'


class Application(TimeStampedModel):
    class ApplicationStatus(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        REVIEWED = 'REVIEWED', 'Reviewed'
        INVITED = 'INVITED', 'Invited'
        HIRED = 'HIRED', 'Hired'
        REJECTED = 'REJECTED', 'Rejected'
        RESERVED = 'RESERVED', 'Reserved'
        
        
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['job_posting', 'applicant']

    def __str__(self):
        return f"{self.applicant} applied for {self.job_posting.title}"


class Assignment(TimeStampedModel):
    class AssignmentStatus(models.TextChoices):
        PENDING_START = 'PENDING_START', 'Pending Start'  # Future
        ACTIVE = 'ACTIVE', 'Active'                      # Present
        COMPLETED = 'COMPLETED', 'Completed'             # Past
        TERMINATED = 'TERMINATED', 'Terminated'          # Past
        PAUSED = 'PAUSED', 'Paused'                      # Present (temporarily inactive)
        CANCELLED = 'CANCELLED', 'Cancelled'             # Past (never started)

    class AssignmentType(models.TextChoices):
        DIRECT_EMPLOYMENT = 'DIRECT_EMPLOYMENT', 'Direct Employment'
        CONTRACTOR = 'CONTRACTOR', 'Contractor'
        TEMPORARY = 'TEMPORARY', 'Temporary Worker'
        CONSULTANT = 'CONSULTANT', 'Consultant'

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='assignments')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.SET_NULL, blank=True, null=True)

    # Enhanced date tracking
    start_date = models.DateField()
    expected_end_date = models.DateField(blank=True, null=True)  # Planned end
    actual_end_date = models.DateField(blank=True, null=True)    # Actual end
    end_date = models.DateField(blank=True, null=True)  # Keep for backward compatibility

    # Status and type
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.PENDING_START)
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices, default=AssignmentType.DIRECT_EMPLOYMENT)

    # Contract and financial
    employment_contract = models.OneToOneField('core.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='assignment')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Additional tracking
    position_title = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    termination_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f"{self.employee.full_name} → {self.employer.company_name} ({self.start_date})"

    @property
    def is_current(self):
        """Check if assignment is currently active"""
        from django.utils import timezone
        today = timezone.now().date()

        if self.status == self.AssignmentStatus.ACTIVE:
            if self.actual_end_date and self.actual_end_date <= today:
                return False
            return self.start_date <= today
        return False

    @property
    def is_future(self):
        """Check if assignment is in the future"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date > today and self.status == self.AssignmentStatus.PENDING_START

    @property
    def is_past(self):
        """Check if assignment is in the past"""
        from django.utils import timezone
        return self.status in [self.AssignmentStatus.COMPLETED, self.AssignmentStatus.TERMINATED, self.AssignmentStatus.CANCELLED] or (
            self.actual_end_date and self.actual_end_date < timezone.now().date()
        )

    @property
    def effective_end_date(self):
        """Get the actual end date or expected end date"""
        return self.actual_end_date or self.expected_end_date or self.end_date

    def get_duration_days(self):
        """Calculate assignment duration in days"""
        from django.utils import timezone
        end_date = self.actual_end_date or self.expected_end_date or self.end_date or timezone.now().date()
        return (end_date - self.start_date).days

    def get_total_hours_worked(self):
        """Calculate total hours worked in this assignment"""
        return sum(
            schedule.total_hours for schedule in self.work_schedules.filter(status='COMPLETED')
        )