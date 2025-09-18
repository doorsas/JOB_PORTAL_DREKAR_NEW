from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import JobPosting, EmployerProfile, Application
from .forms import JobPostingForm, EmployerProfileForm


def is_employer(user):
    return user.is_authenticated and user.user_type == 'EMPLOYER'


@login_required
@user_passes_test(is_employer)
def dashboard(request):
    """Employer dashboard view"""
    context = {
        'user': request.user,
        'has_profile': hasattr(request.user, 'employerprofile'),
    }

    if context['has_profile']:
        context['profile'] = request.user.employerprofile
        employer_profile = request.user.employerprofile

        # Add some basic stats
        context.update({
            'total_job_postings': employer_profile.job_postings.count(),
            'active_job_postings': employer_profile.job_postings.filter(status='OPEN').count(),
            'total_assignments': employer_profile.assignments.count(),
            'active_assignments': employer_profile.assignments.filter(status='ACTIVE').count(),
        })

        # Add recent job postings (last 5)
        recent_jobs = employer_profile.job_postings.order_by('-posted_date')[:5]
        for job in recent_jobs:
            job.applications_count = job.applications.count()
        context['recent_job_postings'] = recent_jobs

    return render(request, 'employers/dashboard.html', context)


@login_required
@user_passes_test(is_employer)
def job_postings_list(request):
    """View and manage job postings"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access job posting features.')
        return redirect('employers:profile_setup')

    # Get all job postings for this employer
    job_postings = JobPosting.objects.filter(employer=employer_profile).order_by('-posted_date')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        job_postings = job_postings.filter(status='OPEN')
    elif status_filter == 'inactive':
        job_postings = job_postings.filter(status__in=['DRAFT', 'CLOSED', 'FILLED'])

    # Pagination
    paginator = Paginator(job_postings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add application counts for each job posting
    for job in page_obj:
        job.applications_count = job.applications.count()
        job.new_applications_count = job.applications.filter(status='SUBMITTED').count()

    context = {
        'page_obj': page_obj,
        'job_postings': page_obj,
        'status_filter': status_filter,
        'employer_profile': employer_profile,
    }

    return render(request, 'employers/jobpostings.html', context)


@login_required
@user_passes_test(is_employer)
def create_job_posting(request):
    """Create a new job posting"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access job posting features.')
        return redirect('employers:profile_setup')

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.employer = employer_profile
            job_posting.save()
            form.save_m2m()  # Save many-to-many fields
            messages.success(request, 'Job posting created successfully!')
            return redirect('employers:job_postings_list')
    else:
        form = JobPostingForm()

    context = {
        'form': form,
        'title': 'Create New Job Posting',
        'action': 'Create'
    }

    return render(request, 'employers/job_posting_form.html', context)


@login_required
@user_passes_test(is_employer)
def edit_job_posting(request, job_id):
    """Edit an existing job posting"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access job posting features.')
        return redirect('employers:profile_setup')

    job_posting = get_object_or_404(JobPosting, id=job_id, employer=employer_profile)

    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job_posting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job posting updated successfully!')
            return redirect('employers:job_postings_list')
    else:
        form = JobPostingForm(instance=job_posting)

    context = {
        'form': form,
        'job_posting': job_posting,
        'title': 'Edit Job Posting',
        'action': 'Update'
    }

    return render(request, 'employers/job_posting_form.html', context)


@login_required
@user_passes_test(is_employer)
def delete_job_posting(request, job_id):
    """Delete a job posting"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access job posting features.')
        return redirect('employers:profile_setup')

    job_posting = get_object_or_404(JobPosting, id=job_id, employer=employer_profile)

    if request.method == 'POST':
        job_posting.delete()
        messages.success(request, 'Job posting deleted successfully!')
        return redirect('employers:job_postings_list')

    context = {
        'job_posting': job_posting
    }

    return render(request, 'employers/confirm_delete.html', context)


@login_required
@user_passes_test(is_employer)
def toggle_job_status(request, job_id):
    """Toggle job posting active/inactive status via AJAX"""
    if request.method == 'POST':
        try:
            employer_profile = request.user.employerprofile
            job_posting = get_object_or_404(JobPosting, id=job_id, employer=employer_profile)

            if job_posting.status == 'OPEN':
                job_posting.status = 'CLOSED'
            else:
                job_posting.status = 'OPEN'
            job_posting.save()

            return JsonResponse({
                'success': True,
                'status': job_posting.status,
                'status_display': job_posting.get_status_display()
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@user_passes_test(is_employer)
def job_posting_detail(request, job_id):
    """View job posting details and applications"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access job posting features.')
        return redirect('employers:profile_setup')

    job_posting = get_object_or_404(JobPosting, id=job_id, employer=employer_profile)
    applications = job_posting.applications.all().order_by('-application_date')

    # Pagination for applications
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    applications_page = paginator.get_page(page_number)

    context = {
        'job_posting': job_posting,
        'applications': applications_page,
        'applications_count': applications.count(),
        'new_applications_count': applications.filter(status='SUBMITTED').count(),
    }

    return render(request, 'employers/job_posting_detail.html', context)


@login_required
@user_passes_test(is_employer)
def profile_setup(request):
    """Create or edit employer profile"""
    try:
        profile = request.user.employerprofile
        is_editing = True
    except EmployerProfile.DoesNotExist:
        profile = None
        is_editing = False

    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            if is_editing:
                messages.success(request, 'Your employer profile has been updated successfully!')
            else:
                messages.success(request, 'Your employer profile has been created successfully! You can now access all employer features.')

            return redirect('employers:dashboard')
    else:
        form = EmployerProfileForm(instance=profile)

    context = {
        'form': form,
        'is_editing': is_editing,
        'title': 'Edit Employer Profile' if is_editing else 'Complete Employer Profile'
    }

    return render(request, 'employers/profile_setup.html', context)


@login_required
@user_passes_test(is_employer)
def profile_view(request):
    """View employer profile"""
    try:
        profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    context = {
        'profile': profile
    }

    return render(request, 'employers/profile_view.html', context)


@login_required
@user_passes_test(is_employer)
def applications_list(request):
    """View all applications for employer's job postings"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access applications.')
        return redirect('employers:profile_setup')

    # Get all applications for this employer's job postings
    applications = Application.objects.filter(
        job_posting__employer=employer_profile
    ).select_related('job_posting', 'applicant', 'applicant__user').order_by('-application_date')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    # Filter by job if requested
    job_filter = request.GET.get('job')
    if job_filter:
        applications = applications.filter(job_posting_id=job_filter)

    # Pagination
    paginator = Paginator(applications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for filter tabs
    status_counts = {
        'all': Application.objects.filter(job_posting__employer=employer_profile).count(),
        'submitted': Application.objects.filter(job_posting__employer=employer_profile, status='SUBMITTED').count(),
        'reviewed': Application.objects.filter(job_posting__employer=employer_profile, status='REVIEWED').count(),
        'invited': Application.objects.filter(job_posting__employer=employer_profile, status='INVITED').count(),
        'hired': Application.objects.filter(job_posting__employer=employer_profile, status='HIRED').count(),
        'rejected': Application.objects.filter(job_posting__employer=employer_profile, status='REJECTED').count(),
    }

    # Get job postings for filter dropdown
    job_postings = JobPosting.objects.filter(employer=employer_profile).order_by('-posted_date')

    context = {
        'page_obj': page_obj,
        'applications': page_obj,
        'status_filter': status_filter,
        'job_filter': job_filter,
        'status_counts': status_counts,
        'job_postings': job_postings,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/applications_list.html', context)


@login_required
@user_passes_test(is_employer)
def application_detail(request, application_id):
    """View detailed application"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile to access applications.')
        return redirect('employers:profile_setup')

    application = get_object_or_404(
        Application,
        id=application_id,
        job_posting__employer=employer_profile
    )

    context = {
        'application': application
    }

    return render(request, 'employers/application_detail.html', context)


@login_required
@user_passes_test(is_employer)
def update_application_status(request, application_id):
    """Update application status"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employers:profile_setup')

    application = get_object_or_404(
        Application,
        id=application_id,
        job_posting__employer=employer_profile
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['SUBMITTED', 'REVIEWED', 'INVITED', 'HIRED', 'REJECTED']:
            application.status = new_status
            application.save()

            status_display = application.get_status_display()
            messages.success(request, f'Application status updated to {status_display}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('employers:application_detail', application_id=application.id)