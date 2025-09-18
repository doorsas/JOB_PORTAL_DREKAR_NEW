from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test


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