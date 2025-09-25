from django import forms
from django.utils.translation import gettext_lazy as _
from .models import JobPosting, EmployerProfile
from core.models import Address, Qualification, Skill, Contract, ContractTemplate


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'required_qualifications', 'required_skills',
            'location', 'num_employees_requested', 'estimated_salary_min',
            'estimated_salary_max', 'closing_date', 'job_type', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter job title'),
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Describe the job requirements, responsibilities, and benefits...'),
                'rows': 6
            }),
            'required_qualifications': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'required_skills': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'num_employees_requested': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'estimated_salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Minimum salary'),
                'step': '0.01'
            }),
            'estimated_salary_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Maximum salary'),
                'step': '0.01'
            }),
            'closing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure we have locations, qualifications, and skills
        if not Address.objects.exists():
            # Add some default locations if none exist
            Address.objects.get_or_create(city='Vilnius', country='Lithuania')
            Address.objects.get_or_create(city='Kaunas', country='Lithuania')
            Address.objects.get_or_create(city='Klaipeda', country='Lithuania')

        # Ensure we have some basic qualifications
        if not Qualification.objects.exists():
            Qualification.objects.get_or_create(name='High School Diploma', defaults={'description': 'Secondary education completion'})
            Qualification.objects.get_or_create(name='Bachelor\'s Degree', defaults={'description': 'University bachelor degree'})
            Qualification.objects.get_or_create(name='Master\'s Degree', defaults={'description': 'University master degree'})
            Qualification.objects.get_or_create(name='Professional Certificate', defaults={'description': 'Professional certification'})

        # Ensure we have some basic skills
        if not Skill.objects.exists():
            Skill.objects.get_or_create(name='Communication', defaults={'description': 'Verbal and written communication skills'})
            Skill.objects.get_or_create(name='Teamwork', defaults={'description': 'Ability to work in team environment'})
            Skill.objects.get_or_create(name='Problem Solving', defaults={'description': 'Analytical and problem-solving abilities'})
            Skill.objects.get_or_create(name='Computer Skills', defaults={'description': 'Basic computer and software skills'})
            Skill.objects.get_or_create(name='Time Management', defaults={'description': 'Ability to manage time effectively'})

        # Make salary fields optional in form
        self.fields['estimated_salary_min'].required = False
        self.fields['estimated_salary_max'].required = False
        self.fields['closing_date'].required = False

        # Add help text
        self.fields['title'].help_text = _('A clear, descriptive job title')
        self.fields['description'].help_text = _('Detailed job description including responsibilities and requirements')
        self.fields['num_employees_requested'].help_text = _('Number of people you want to hire for this position')
        self.fields['estimated_salary_min'].help_text = _('Minimum salary (optional)')
        self.fields['estimated_salary_max'].help_text = _('Maximum salary (optional)')

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('estimated_salary_min')
        salary_max = cleaned_data.get('estimated_salary_max')

        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(
                _('Minimum salary cannot be greater than maximum salary.')
            )

        return cleaned_data


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = [
            'company_name', 'registration_code', 'phone', 'website',
            'contact_person_name', 'contact_person_email', 'contact_person_phone', 'logo'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your company name'),
                'maxlength': 200
            }),
            'registration_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('VAT ID, Registration Number, etc.'),
                'maxlength': 50
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Company phone number'),
                'maxlength': 20
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('https://www.yourcompany.com')
            }),
            'contact_person_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Contact person full name'),
                'maxlength': 100
            }),
            'contact_person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('contact@company.com')
            }),
            'contact_person_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Contact person phone'),
                'maxlength': 20
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add address field dynamically to avoid circular import issues
        from django import forms
        self.fields['address'] = forms.ModelChoiceField(
            queryset=Address.objects.all(),
            required=False,
            empty_label=_('Select an address or create one'),
            widget=forms.Select(attrs={'class': 'form-control'})
        )

        # Create some default addresses if none exist
        if not Address.objects.exists():
            Address.objects.create(
                street_address='Main Street 1',
                city='Vilnius',
                postal_code='01234',
                country='Lithuania'
            )
            Address.objects.create(
                street_address='Business Street 5',
                city='Kaunas',
                postal_code='44444',
                country='Lithuania'
            )
            self.fields['address'].queryset = Address.objects.all()

        # Add help text
        self.fields['company_name'].help_text = _('Legal name of your company')
        self.fields['registration_code'].help_text = _('VAT ID, business registration number, or tax ID')
        self.fields['address'].help_text = _('Company headquarters or main office address')
        self.fields['website'].help_text = _('Company website (optional)')
        self.fields['contact_person_name'].help_text = _('Main contact person for HR matters')
        self.fields['contact_person_email'].help_text = _('Email for HR and recruitment communications')
        self.fields['contact_person_phone'].help_text = _('Phone number for urgent HR matters')
        self.fields['logo'].help_text = _('Company logo (will be automatically resized to 200x200px)')

        # Set required fields
        self.fields['website'].required = False
        self.fields['logo'].required = False

    def clean_contact_person_email(self):
        email = self.cleaned_data.get('contact_person_email')
        if email:
            # Check if this email is different from user's email or if it's a business email
            if not email.lower().endswith(('.com', '.net', '.org', '.biz', '.co')):
                raise forms.ValidationError(
                    _('Please provide a valid business email address.')
                )
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 7:
                raise forms.ValidationError(
                    _('Please provide a valid phone number.')
                )
        return phone

    def clean_contact_person_phone(self):
        phone = self.cleaned_data.get('contact_person_phone')
        if phone:
            # Basic phone validation
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 7:
                raise forms.ValidationError(
                    _('Please provide a valid contact phone number.')
                )
        return phone

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle the address field separately since it's dynamically added
        address = self.cleaned_data.get('address')
        if address:
            instance.address = address

        if commit:
            instance.save()
        return instance


class ContractForm(forms.ModelForm):
    """Form for creating and editing contracts"""

    class Meta:
        model = Contract
        fields = [
            'contract_type', 'template_used', 'effective_date',
            'expiry_date', 'document_file'
        ]
        widgets = {
            'contract_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'template_used': forms.Select(attrs={
                'class': 'form-control'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'document_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter active templates only
        self.fields['template_used'].queryset = ContractTemplate.objects.filter(is_active=True)
        self.fields['template_used'].empty_label = _('Select a template (optional)')

        # Add help text
        self.fields['contract_type'].help_text = _('Type of contract you want to create')
        self.fields['template_used'].help_text = _('Pre-defined template to use as a base (optional)')
        self.fields['effective_date'].help_text = _('When this contract becomes effective')
        self.fields['expiry_date'].help_text = _('When this contract expires (optional for indefinite contracts)')
        self.fields['document_file'].help_text = _('Upload signed contract document (PDF recommended)')

        # Set field labels
        self.fields['contract_type'].label = _('Contract Type')
        self.fields['template_used'].label = _('Contract Template')
        self.fields['effective_date'].label = _('Effective Date')
        self.fields['expiry_date'].label = _('Expiry Date')
        self.fields['document_file'].label = _('Contract Document')

    def clean_expiry_date(self):
        """Validate that expiry date is after effective date"""
        effective_date = self.cleaned_data.get('effective_date')
        expiry_date = self.cleaned_data.get('expiry_date')

        if effective_date and expiry_date:
            if expiry_date <= effective_date:
                raise forms.ValidationError(
                    _('Expiry date must be after the effective date.')
                )

        return expiry_date

    def clean_document_file(self):
        """Validate uploaded document file"""
        document_file = self.cleaned_data.get('document_file')

        if document_file:
            # Check file size (max 10MB)
            if document_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    _('File size cannot exceed 10MB.')
                )

            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx']
            file_name = document_file.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(
                    _('Only PDF, DOC, and DOCX files are allowed.')
                )

        return document_file