from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

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
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    registration_code = models.CharField(max_length=100)
    address = models.ForeignKey('core.Address', on_delete=models.SET_NULL, null=True, blank=True)
    contact_person_name = models.CharField(max_length=200)
    contact_person_email = models.EmailField()

    class Meta:
        abstract = True


        
class Address(TimeStampedModel):
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100) # For advanced needs, consider a package like django-countries

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"


class ContractTemplate(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    contract_type = models.CharField(max_length=50) # e.g., 'SERVICE_AGREEMENT', 'EOR_AGREEMENT'
    content = models.TextField(help_text="Standard contract text with placeholders.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ['city', 'country']

    def __str__(self):
        return f"{self.city}, {self.country}"


class Qualification(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


from django.core.exceptions import ValidationError

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

    # Explicit links instead of GenericForeignKey for simplicity
    employer_profile = models.ForeignKey('employers.EmployerProfile', on_delete=models.CASCADE, null=True, blank=True)
    eor_client_profile = models.ForeignKey('eor_services.EORClientProfile', on_delete=models.CASCADE, null=True, blank=True)

    template_used = models.ForeignKey(ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    signed_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document_file = models.FileField(upload_to='contracts/%Y/%m/', help_text="The signed PDF document.")

    def clean(self):
        # Ensure that the contract is linked to exactly one type of client
        if not (self.employer_profile or self.eor_client_profile):
            raise ValidationError("Contract must be linked to either an Employer or an EOR Client.")
        if self.employer_profile and self.eor_client_profile:
            raise ValidationError("Contract cannot be linked to both an Employer and an EOR Client.")
        
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Invoice(TimeStampedModel):
    class InvoiceStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELED = 'CANCELED', 'Canceled'

    # Client can be Employer or EOR Client (also a good case for GenericForeignKey)
    client_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    client_object_id = models.PositiveIntegerField()
    client = GenericForeignKey('client_content_type', 'client_object_id')

    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING)
    pdf_file = models.FileField(upload_to='invoices/%Y/%m/', null=True, blank=True)
    # REMOVE: amount = models.DecimalField(...)

    @property
    def total_amount(self):
        return sum(item.total for item in self.line_items.all())

class SalaryBenchmark(TimeStampedModel):
    profession = models.ForeignKey('Profession', on_delete=models.CASCADE)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    experience_level = models.CharField(max_length=50, choices=[('ENTRY', 'Entry'), ('MID', 'Mid-Level'), ('SENIOR', 'Senior')])
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    data_source = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('profession', 'location', 'experience_level')

class Payment(models.Model):
    METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('XML_INTEGRATION', 'XML Integration'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CASH', 'Cash'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Payment {self.amount_paid} for {self.invoice.invoice_number}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('INVOICE_REMINDER', 'Invoice Reminder'),
        ('STATUS_UPDATE', 'Status Update'),
        ('APPLICATION_UPDATE', 'Application Update'),
        ('PAYSLIP_READY', 'Payslip Ready'),
        ('CONTRACT_EXPIRY', 'Contract Expiry'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.email}"


class Profession(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.name
    
class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey('Invoice', related_name='line_items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.unit_price