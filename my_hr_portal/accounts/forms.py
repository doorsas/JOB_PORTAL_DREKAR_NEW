from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text=_("Required. Enter a valid email address.")
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=True,
        help_text=_("Select your account type.")
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        help_text=_("Required.")
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        help_text=_("Required.")
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'user_type', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes and attributes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
            })

        # Email should be the primary field
        self.fields['email'].widget.attrs.update({
            'placeholder': _('Enter your email address'),
            'autofocus': True
        })
        self.fields['username'].widget.attrs.update({
            'placeholder': _('Choose a username')
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': _('First name')
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': _('Last name')
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': _('Create a password')
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': _('Confirm your password')
        })

    def save(self, commit=True):
            user = super().save(commit=False)
            user.email = self.cleaned_data['email']
            user.user_type = self.cleaned_data['user_type']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.set_password(self.cleaned_data['password1'])
            if commit:
                user.save()
            return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your password')
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the username field to accept email
        self.fields['username'].label = _("Email")

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            # Try to authenticate with email instead of username
            try:
                self.user_cache = authenticate(
                    self.request,
                    username=email,
                    password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError(
                        _("Please enter a correct email and password."),
                        code='invalid_login',
                    )
                else:
                    self.confirm_login_allowed(self.user_cache)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _("Please enter a correct email and password."),
                    code='invalid_login',
                )

        return self.cleaned_data