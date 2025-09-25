from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


# 1. ABSTRACT BASE MODELS (Excellent implementation)
# ===================================================
class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_at` and `updated_at` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    class Meta:
        abstract = True


class BaseClientProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    registration_code = models.CharField(max_length=100)
    address = models.ForeignKey('core.Address', on_delete=models.SET_NULL, null=True, blank=True)
    contact_person_name = models.CharField(max_length=200)
    contact_person_email = models.EmailField()

    class Meta:
        abstract = True


# 2. CORE DATA MODELS
# ===================================================

# SUGGESTION: Merged 'Location' into 'Address' for simplicity
class Address(TimeStampedModel):
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Addresses"
        unique_together = ['street_address', 'city', 'country']

    def __str__(self):
        if self.street_address:
            return f"{self.street_address}, {self.city}, {self.country}"
        return f"{self.city}, {self.country}"


# FIX: Moved Profession model up to resolve dependency
# SUGGESTION: Inherits TimeStampedModel for consistency
class Profession(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# SUGGESTION: Inherits TimeStampedModel for consistency
class Qualification(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# SUGGESTION: Inherits TimeStampedModel for consistency
class Skill(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class ContractTemplate(TimeStampedModel):
    # SUGGESTION: Use TextChoices for consistency
    class TemplateType(models.TextChoices):
        SERVICE_AGREEMENT = 'SERVICE_AGREEMENT', 'Service Agreement'
        EOR_AGREEMENT = 'EOR_AGREEMENT', 'EOR Agreement'
        EMPLOYMENT_CONTRACT = 'EMPLOYMENT_CONTRACT', 'Employment Contract'

    name = models.CharField(max_length=200, unique=True)
    contract_type = models.CharField(max_length=50, choices=TemplateType.choices)
    content = models.TextField(help_text="Standard contract text with placeholders.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SalaryBenchmark(TimeStampedModel):
    # SUGGESTION: Use TextChoices for consistency
    class ExperienceLevel(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry'
        MID = 'MID', 'Mid-Level'
        SENIOR = 'SENIOR', 'Senior'

    
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name='benchmarks')
    # Note: Assumes you merged 'Location' into 'Address'
    location = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='benchmarks')
    experience_level = models.CharField(max_length=50, choices=ExperienceLevel.choices)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    data_source = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('profession', 'location', 'experience_level')
        
    def __str__(self):
        return f"{self.profession.name} in {self.location.city} ({self.get_experience_level_display()})"


# 3. TRANSACTIONAL & LOGIC MODELS
# ===================================================

class Contract(TimeStampedModel):
    class ContractType(models.TextChoices):
        SERVICE_AGREEMENT = 'SERVICE_AGREEMENT', 'Service Agreement'
        EOR_AGREEMENT = 'EOR_AGREEMENT', 'EOR Agreement'
        EMPLOYMENT_CONTRACT = 'EMPLOYMENT_CONTRACT', 'Employment Contract'

    class ContractStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_SIGNATURE = 'PENDING_SIGNATURE', 'Pending Signature'
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    contract_type = models.CharField(max_length=50, choices=ContractType.choices)
    status = models.CharField(max_length=50, choices=ContractStatus.choices, default=ContractStatus.DRAFT)

    employer_profile = models.ForeignKey('employers.EmployerProfile', on_delete=models.CASCADE, null=True, blank=True)
    eor_client_profile = models.ForeignKey('eor_services.EORClientProfile', on_delete=models.CASCADE, null=True, blank=True)

    template_used = models.ForeignKey(ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    signed_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document_file = models.FileField(upload_to='contracts/%Y/%m/', help_text="The signed PDF document.", null=True, blank=True)

    def clean(self):
        client_profiles = [self.employer_profile, self.eor_client_profile]
        if sum(p is not None for p in client_profiles) != 1:
            raise ValidationError("Contract must be linked to exactly one client profile (Employer or EOR).")

    def __str__(self):
        client_name = ""
        if self.employer_profile:
            client_name = self.employer_profile.company_name
        elif self.eor_client_profile:
            client_name = self.eor_client_profile.company_name
        return f"{self.get_contract_type_display()} for {client_name}"

class Invoice(TimeStampedModel):
    class InvoiceStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELED = 'CANCELED', 'Canceled'

    client_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    client_object_id = models.PositiveIntegerField()
    client = GenericForeignKey('client_content_type', 'client_object_id')

    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING)
    pdf_file = models.FileField(upload_to='invoices/%Y/%m/', null=True, blank=True)

    @property
    def total_amount(self):
        if hasattr(self, '_total_amount'):
             return self._total_amount
        return sum(item.total for item in self.line_items.all())


# SUGGESTION: Inherits TimeStampedModel for consistency
class InvoiceLineItem(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.unit_price


# SUGGESTION: Inherits TimeStampedModel for timestamps
class Payment(TimeStampedModel):
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        XML_INTEGRATION = 'XML_INTEGRATION', 'XML Integration'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'

    class PaymentStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)

    def __str__(self):
        return f"Payment of {self.amount_paid} for Invoice {self.invoice.invoice_number}"


# SUGGESTION: Inherits TimeStampedModel and removes manual `created_at`
class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        INVOICE_REMINDER = 'INVOICE_REMINDER', 'Invoice Reminder'
        STATUS_UPDATE = 'STATUS_UPDATE', 'Status Update'
        APPLICATION_UPDATE = 'APPLICATION_UPDATE', 'Application Update'
        PAYSLIP_READY = 'PAYSLIP_READY', 'Payslip Ready'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    # The 'created_at' and 'updated_at' fields are inherited from TimeStampedModel

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient}"