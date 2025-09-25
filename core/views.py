from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Homepage view"""
    context = {
        'user': request.user,
    }

    # Add different content based on user authentication
    if request.user.is_authenticated:
        context.update({
            'show_dashboard_link': True,
            'user_type': request.user.user_type,
            'user_type_display': request.user.get_user_type_display(),
        })

    return render(request, 'core/home.html', context)


def about(request):
    """About page view"""
    return render(request, 'core/about.html')


def services(request):
    """Services page view"""
    return render(request, 'core/services.html')


@login_required
def dashboard(request):
    """General dashboard view that redirects to role-specific dashboards"""
    # This view should redirect users to their specific dashboard
    # but for now, we'll show a generic dashboard
    if request.user.user_type == 'EMPLOYER':
        from django.shortcuts import redirect
        return redirect('employers:dashboard')
    elif request.user.user_type == 'EMPLOYEE':
        from django.shortcuts import redirect
        return redirect('employees:dashboard')
    elif request.user.user_type == 'EOR_CLIENT':
        from django.shortcuts import redirect
        return redirect('eor_services:dashboard')
    elif request.user.user_type == 'ADMIN':
        from django.shortcuts import redirect
        return redirect('admin:index')

    # Fallback for undefined user types
    context = {
        'user': request.user,
        'user_type': request.user.user_type,
        'user_type_display': request.user.get_user_type_display(),
    }
    return render(request, 'core/dashboard.html', context)