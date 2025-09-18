from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import EmployeeProfile, Document
from core.models import Skill, Profession, Address
from employers.models import JobPosting, Application
import datetime


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'phone',
            'nationality', 'preferred_professions', 'skills', 'experience_summary',
            'expected_salary', 'current_status'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your first name'),
                'maxlength': 50
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your last name'),
                'maxlength': 50
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your phone number'),
                'maxlength': 20
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your nationality'),
                'maxlength': 50
            }),
            'preferred_professions': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'skills': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'experience_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Describe your work experience, achievements, and career highlights...'),
                'rows': 5
            }),
            'expected_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Expected monthly salary (EUR)'),
                'step': '100',
                'min': '0'
            }),
            'current_status': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add address field dynamically to avoid circular import issues
        from django import forms
        self.fields['address'] = forms.ModelChoiceField(
            queryset=Address.objects.all(),
            required=False,
            empty_label=_('Select an address'),
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

        # Create some default professions and skills if they don't exist
        self._ensure_default_data()

        # Add help text
        self.fields['first_name'].help_text = _('Your first name as it appears on official documents')
        self.fields['last_name'].help_text = _('Your last name as it appears on official documents')
        self.fields['date_of_birth'].help_text = _('Your date of birth (required for employment verification)')
        self.fields['address'].help_text = _('Your current residential address')
        self.fields['phone'].help_text = _('Your primary contact phone number')
        self.fields['nationality'].help_text = _('Your nationality for work permit purposes')
        self.fields['preferred_professions'].help_text = _('Select the types of jobs you are interested in')
        self.fields['skills'].help_text = _('Select your professional skills and competencies')
        self.fields['experience_summary'].help_text = _('Summarize your work experience and key achievements')
        self.fields['expected_salary'].help_text = _('Your expected monthly salary in EUR (optional)')
        self.fields['current_status'].help_text = _('Your current employment availability')

        # Set required fields
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'phone', 'nationality']
        for field_name in required_fields:
            self.fields[field_name].required = True

        # Optional fields
        self.fields['expected_salary'].required = False
        self.fields['experience_summary'].required = False

        # Set max date for date of birth (must be at least 16 years old)
        max_date = datetime.date.today() - datetime.timedelta(days=16*365)
        self.fields['date_of_birth'].widget.attrs['max'] = max_date.strftime('%Y-%m-%d')

    def _ensure_default_data(self):
        """Create some default professions and skills if they don't exist"""
        # Default professions
        default_professions = [
            'Software Developer', 'Sales Representative', 'Customer Service',
            'Marketing Specialist', 'Administrative Assistant', 'Project Manager',
            'Financial Analyst', 'HR Specialist', 'Graphic Designer', 'Data Analyst'
        ]

        for prof_name in default_professions:
            Profession.objects.get_or_create(name=prof_name)

        # Default skills
        default_skills = [
            ('Communication', 'Soft Skills'), ('Problem Solving', 'Soft Skills'),
            ('Team Work', 'Soft Skills'), ('Leadership', 'Soft Skills'),
            ('Microsoft Office', 'Technical'), ('Excel', 'Technical'),
            ('PowerPoint', 'Technical'), ('Project Management', 'Technical'),
            ('Customer Service', 'Professional'), ('Sales', 'Professional'),
            ('Marketing', 'Professional'), ('Data Analysis', 'Technical'),
            ('Social Media', 'Digital'), ('Content Writing', 'Professional')
        ]

        for skill_name, category in default_skills:
            Skill.objects.get_or_create(name=skill_name, defaults={'category': category})

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age < 16:
                raise ValidationError(_('You must be at least 16 years old to register.'))
            if age > 100:
                raise ValidationError(_('Please enter a valid date of birth.'))

        return dob

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 7:
                raise ValidationError(_('Please provide a valid phone number.'))
        return phone


    def clean_expected_salary(self):
        salary = self.cleaned_data.get('expected_salary')
        if salary is not None:
            if salary < 0:
                raise ValidationError(_('Expected salary cannot be negative.'))
            if salary > 100000:
                raise ValidationError(_('Please enter a reasonable expected salary.'))
        return salary

    def clean(self):
        cleaned_data = super().clean()

        # Check if at least one skill or profession is selected
        skills = cleaned_data.get('skills')
        professions = cleaned_data.get('preferred_professions')

        if not skills and not professions:
            raise ValidationError(
                _('Please select at least one skill or preferred profession to help employers find you.')
            )

        return cleaned_data


class JobSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search for jobs, companies, or skills...'),
            'autocomplete': 'off'
        }),
        label=_('Search')
    )

    location = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_('All Locations'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Location')
    )

    job_type = forms.ChoiceField(
        choices=[('', _('All Types'))] + JobPosting.JOB_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Job Type')
    )

    min_salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Minimum salary'),
            'step': '100'
        }),
        label=_('Minimum Salary (EUR)')
    )

    skills = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label=_('Required Skills')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from core.models import Location

        # Set querysets
        self.fields['location'].queryset = Location.objects.all().order_by('city')
        self.fields['skills'].queryset = Skill.objects.all().order_by('name')


class JobApplicationForm(forms.ModelForm):
    cover_letter = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _('Write a cover letter explaining why you are interested in this position and why you would be a good fit...'),
            'rows': 6
        }),
        required=False,
        label=_('Cover Letter'),
        help_text=_('Optional: Explain why you are interested in this position')
    )

    class Meta:
        model = Application
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Any additional notes or comments...'),
                'rows': 3
            })
        }
        labels = {
            'notes': _('Additional Notes')
        }

    def __init__(self, *args, **kwargs):
        self.job_posting = kwargs.pop('job_posting', None)
        self.employee_profile = kwargs.pop('employee_profile', None)
        super().__init__(*args, **kwargs)

        # Make notes field optional
        self.fields['notes'].required = False
        self.fields['notes'].help_text = _('Optional: Any additional information you want to share with the employer')

    def clean(self):
        cleaned_data = super().clean()

        # Check if user has already applied for this job
        if self.job_posting and self.employee_profile:
            existing_application = Application.objects.filter(
                job_posting=self.job_posting,
                applicant=self.employee_profile
            ).exists()

            if existing_application:
                raise ValidationError(
                    _('You have already applied for this position.')
                )

        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=False)
        application.job_posting = self.job_posting
        application.applicant = self.employee_profile

        # Combine cover letter and notes
        cover_letter = self.cleaned_data.get('cover_letter', '')
        additional_notes = self.cleaned_data.get('notes', '')

        if cover_letter and additional_notes:
            application.notes = f"Cover Letter:\n{cover_letter}\n\nAdditional Notes:\n{additional_notes}"
        elif cover_letter:
            application.notes = f"Cover Letter:\n{cover_letter}"
        elif additional_notes:
            application.notes = additional_notes

        if commit:
            application.save()

        return application


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Optional description for this document')
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['file'].help_text = _('Upload document (PDF, DOC, DOCX or JPG format, max 5MB)')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('File size must be less than 5MB.'))

            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(
                    _('Only PDF, DOC, DOCX and JPG files are allowed.')
                )

        return file