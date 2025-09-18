from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import User


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # Redirect based on user type
        print (self.request.user.user_type)
        if self.request.user.user_type == 'EMPLOYER':
            return reverse_lazy('employers:dashboard')
        elif self.request.user.user_type == 'EMPLOYEE':
            return reverse_lazy('employees:dashboard')
        elif self.request.user.user_type == 'EOR_CLIENT':
            return reverse_lazy('eor_services:dashboard')
        elif self.request.user.user_type == 'ADMIN':
            return reverse_lazy('admin:index')
        else:
            return reverse_lazy('core:home')

    def form_valid(self, form):
        messages.success(self.request, _('Welcome back!'))
        return super().form_valid(form)


class CustomRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Account created successfully! You can now log in.')
        )
        # Optionally auto-login the user after registration
        # login(self.request, self.object)
        # return redirect(self.get_success_url())
        return response

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)


def logout_view(request):
    """Custom logout view that handles both GET and POST requests"""
    from django.contrib.auth import logout

    if request.user.is_authenticated:
        logout(request)
        messages.success(request, _('You have been logged out successfully.'))

    return render(request, 'accounts/logout.html')


@login_required
def profile_view(request):
    """Display and edit user profile"""
    context = {
        'user': request.user,
    }

    # Add user type specific information
    if hasattr(request.user, 'employerprofile'):
        context['profile'] = request.user.employerprofile
        context['profile_type'] = 'employer'
    elif hasattr(request.user, 'employeeprofile'):
        context['profile'] = request.user.employeeprofile
        context['profile_type'] = 'employee'
    elif hasattr(request.user, 'eorclientprofile'):
        context['profile'] = request.user.eorclientprofile
        context['profile_type'] = 'eor_client'

    return render(request, 'accounts/profile.html', context)


def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on user type"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if request.user.user_type == 'EMPLOYER':
        return redirect('employers:dashboard')
    elif request.user.user_type == 'EMPLOYEE':
        return redirect('employees:dashboard')
    elif request.user.user_type == 'EOR_CLIENT':
        return redirect('eor_services:dashboard')
    elif request.user.user_type == 'ADMIN':
        return redirect('admin:index')
    else:
        return redirect('core:home')