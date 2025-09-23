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
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        PENDING_START = 'PENDING_START', 'Pending Start'
        TERMINATED = 'TERMINATED', 'Terminated'

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey('employees.EmployeeProfile', on_delete=models.CASCADE, related_name='assignments')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.PENDING_START)
    employment_contract = models.OneToOneField('core.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='assignment')

    def __str__(self):
        return f"{self.employee} assigned to {self.employer.company_name}"