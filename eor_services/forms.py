from django import forms
from django.utils.translation import gettext_lazy as _
from .models import EORClientProfile
from core.models import Address


class EORClientProfileForm(forms.ModelForm):
    class Meta:
        model = EORClientProfile
        fields = [
            'company_name', 'registration_code',
            'contact_person_name', 'contact_person_email'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your company name'),
                'maxlength': 255
            }),
            'registration_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Company registration number or VAT ID'),
                'maxlength': 100
            }),
            'contact_person_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Contact person full name'),
                'maxlength': 200
            }),
            'contact_person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('contact@company.com')
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add address field dynamically to avoid circular import issues
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

        # Add help text for all fields
        self.fields['company_name'].help_text = _('Legal name of your company')
        self.fields['registration_code'].help_text = _('VAT ID, business registration number, or tax ID')
        self.fields['address'].help_text = _('Company headquarters or main office address')
        self.fields['contact_person_name'].help_text = _('Main contact person for EOR services')
        self.fields['contact_person_email'].help_text = _('Email for EOR service communications')

    def clean_contact_person_email(self):
        email = self.cleaned_data.get('contact_person_email')
        if email:
            # Check if this email is a valid business email
            if not email.lower().endswith(('.com', '.net', '.org', '.biz', '.co')):
                raise forms.ValidationError(
                    _('Please provide a valid business email address.')
                )
        return email

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle the address field separately since it's dynamically added
        address = self.cleaned_data.get('address')
        if address:
            instance.address = address

        if commit:
            instance.save()
        return instance