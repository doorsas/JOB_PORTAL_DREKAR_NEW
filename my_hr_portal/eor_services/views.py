from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import EORClientProfile
from .forms import EORClientProfileForm


def is_eor_client(user):
    return user.is_authenticated and user.user_type == 'EOR_CLIENT'


@login_required
@user_passes_test(is_eor_client)
def dashboard(request):
    """EOR Client dashboard view"""
    context = {
        'user': request.user,
        'has_profile': hasattr(request.user, 'eorclientprofile'),
    }

    if context['has_profile']:
        context['profile'] = request.user.eorclientprofile
        # Add some basic stats
        context.update({
            'total_agreements': request.user.eorclientprofile.eor_agreements.count(),
            'active_agreements': request.user.eorclientprofile.eor_agreements.filter(status='ACTIVE').count(),
            'total_placements': request.user.eorclientprofile.eor_placements.count(),
            'active_placements': request.user.eorclientprofile.eor_placements.filter(status='ACTIVE').count(),
        })

    return render(request, 'eor_services/dashboard.html', context)


@login_required
@user_passes_test(is_eor_client)
def profile_setup(request):
    """Create or edit EOR client profile"""
    try:
        profile = request.user.eorclientprofile
        is_editing = True
    except EORClientProfile.DoesNotExist:
        profile = None
        is_editing = False

    if request.method == 'POST':
        form = EORClientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            if is_editing:
                messages.success(request, 'Your EOR client profile has been updated successfully!')
            else:
                messages.success(request, 'Your EOR client profile has been created successfully! You can now access all EOR services.')

            return redirect('eor_services:dashboard')
    else:
        form = EORClientProfileForm(instance=profile)

    context = {
        'form': form,
        'is_editing': is_editing,
        'title': 'Edit EOR Client Profile' if is_editing else 'Complete EOR Client Profile'
    }

    return render(request, 'eor_services/profile_setup.html', context)


@login_required
@user_passes_test(is_eor_client)
def profile_view(request):
    """View EOR client profile"""
    try:
        profile = request.user.eorclientprofile
    except EORClientProfile.DoesNotExist:
        messages.info(request, 'Please complete your EOR client profile first.')
        return redirect('eor_services:profile_setup')

    context = {
        'profile': profile
    }

    return render(request, 'eor_services/profile_view.html', context)