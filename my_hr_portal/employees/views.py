
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import EmployeeProfile, Document,Payslip,WorkSchedule,Timesheet
from .forms import EmployeeProfileForm, JobSearchForm, JobApplicationForm, DocumentUploadForm,WorkScheduleForm, TimesheetForm
from employers.models import JobPosting, Application
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.utils import timezone

def is_employee(user):
    return user.is_authenticated and user.user_type == 'EMPLOYEE'

# Payslips page for employees
@login_required
@user_passes_test(is_employee)
def payslips_view(request):
    profile = getattr(request.user, 'employeeprofile', None)
    payslips = profile.payslips.order_by('-issue_date') if profile else []
    return render(request, 'employees/payslips.html', {'payslips': payslips})

class WorkScheduleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = 'employees/schedule_form.html'
    success_url = '/schedules/' # Redirect to a schedule list page

    def test_func(self):
        # Only allow managers to access this view
        return self.request.user.is_staff # Or a more specific 'is_manager' check




@login_required
def process_timesheet(request, timesheet_id, action):
    if not request.user.is_staff:
        return redirect('dashboard') # Or show an error

    timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    if request.method == 'POST':
        if action == 'approve':
            timesheet.status = 'APPROVED'
            timesheet.approved_by = request.user
            timesheet.approval_date = timezone.now()
        elif action == 'reject':
            timesheet.status = 'REJECTED'

        timesheet.save()
    return redirect('pending_timesheets')



class PendingTimesheetsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Timesheet
    template_name = 'employees/pending_timesheets.html'
    context_object_name = 'timesheets'

    def get_queryset(self):
        # Managers should only see timesheets for their employees
        return Timesheet.objects.filter(status='PENDING').order_by('date')

    def test_func(self):
        return self.request.user.is_staff

@login_required
def submit_timesheet(request, schedule_id=None):
    initial_data = {}
    schedule = None
    if schedule_id:
        schedule = get_object_or_404(WorkSchedule, id=schedule_id, employee__user=request.user)
        initial_data = {
            'date': schedule.date,
            'hours_worked': round(schedule.total_hours, 2)
        }

    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            timesheet = form.save(commit=False)
            timesheet.employee = request.user.employeeprofile
            timesheet.work_schedule = schedule
            timesheet.save()
            # Optional: Update the WorkSchedule status
            if schedule:
                schedule.status = 'COMPLETED'
                schedule.save()
            return redirect('my_timesheets_list')
    else:
        form = TimesheetForm(initial=initial_data)

    return render(request, 'employees/timesheet_form.html', {'form': form, 'schedule': schedule})

@login_required
@user_passes_test(is_employee)
def dashboard(request):
    """Employee dashboard view"""
    context = {
        'user': request.user,
        'has_profile': hasattr(request.user, 'employeeprofile'),
    }

    if context['has_profile']:
        profile = request.user.employeeprofile
        context['profile'] = profile

        # Check if CV is uploaded
        cv_document = Document.objects.filter(
            employee=profile,
            document_type=Document.DocumentType.CV
        ).order_by('-created_at').first()
        context['has_cv'] = cv_document is not None

        # Add some basic stats
        context.update({
            'total_applications': profile.applications.count(),
            'pending_applications': profile.applications.filter(status='SUBMITTED').count(),
            'total_assignments': profile.assignments.count(),
            'active_assignments': profile.assignments.filter(status='ACTIVE').count(),
            'payslips': profile.payslips.order_by('-issue_date') if hasattr(profile, 'payslips') else [],
        })

    return render(request, 'employees/dashboard.html', context)


@login_required
@user_passes_test(is_employee)
def profile_setup(request):
    """Create or edit employee profile"""
    try:
        profile = request.user.employeeprofile
        is_editing = True
    except EmployeeProfile.DoesNotExist:
        profile = None
        is_editing = False

    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            form.save_m2m()  # Save many-to-many fields

            if is_editing:
                messages.success(request, 'Your employee profile has been updated successfully!')
            else:
                messages.success(request, 'Your employee profile has been created successfully! You can now apply for jobs and access all features.')

            return redirect('employees:dashboard')
    else:
        form = EmployeeProfileForm(instance=profile)

        # Auto-fill user data if creating new profile
        if not is_editing:
            form.fields['first_name'].initial = request.user.first_name
            form.fields['last_name'].initial = request.user.last_name

    context = {
        'form': form,
        'is_editing': is_editing,
        'title': 'Edit Employee Profile' if is_editing else 'Complete Employee Profile'
    }

    return render(request, 'employees/profile_setup.html', context)


@login_required
@user_passes_test(is_employee)
def profile_view(request):
    """View employee profile"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.info(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    # Get the latest CV document
    cv_document = Document.objects.filter(
        employee=profile,
        document_type=Document.DocumentType.CV
    ).order_by('-created_at').first()

    context = {
        'profile': profile,
        'cv_document': cv_document
    }

    return render(request, 'employees/profile_view.html', context)


@login_required
@user_passes_test(is_employee)
def cv_download(request):
    """Download CV file"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    # Get the latest CV document
    cv_document = Document.objects.filter(
        employee=profile,
        document_type=Document.DocumentType.CV
    ).order_by('-created_at').first()

    if not cv_document:
        messages.error(request, 'No CV file uploaded.')
        return redirect('employees:profile_view')

    try:
        response = HttpResponse(cv_document.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{cv_document.file.name}"'
        return response
    except FileNotFoundError:
        messages.error(request, 'CV file not found.')
        return redirect('employees:profile_view')


@login_required
@user_passes_test(is_employee)
def job_search(request):
    """Search for available job postings"""
    form = JobSearchForm(request.GET or None)
    jobs = JobPosting.objects.filter(status='OPEN').select_related('employer', 'location').prefetch_related('required_skills', 'required_qualifications')

    # Apply search filters
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        location = form.cleaned_data.get('location')
        job_type = form.cleaned_data.get('job_type')
        min_salary = form.cleaned_data.get('min_salary')
        skills = form.cleaned_data.get('skills')

        if search_query:
            jobs = jobs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(employer__company_name__icontains=search_query)
            )

        if location:
            jobs = jobs.filter(location=location)

        if job_type:
            jobs = jobs.filter(job_type=job_type)

        if min_salary:
            jobs = jobs.filter(
                Q(estimated_salary_min__gte=min_salary) |
                Q(estimated_salary_max__gte=min_salary)
            )

        if skills:
            jobs = jobs.filter(required_skills__in=skills).distinct()

    # Order by creation date (newest first)
    jobs = jobs.order_by('-created_at')

    # Add application status for each job if user has profile
    try:
        employee_profile = request.user.employeeprofile
        for job in jobs:
            job.user_applied = Application.objects.filter(
                job_posting=job,
                applicant=employee_profile
            ).exists()
    except EmployeeProfile.DoesNotExist:
        for job in jobs:
            job.user_applied = False

    # Pagination
    paginator = Paginator(jobs, 12)  # 12 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'jobs': page_obj,
        'total_jobs': jobs.count()
    }

    return render(request, 'employees/job_search.html', context)


@login_required
@user_passes_test(is_employee)
def job_detail(request, job_id):
    """View detailed job posting"""
    job = get_object_or_404(JobPosting, id=job_id, status='OPEN')

    # Check if user has applied
    user_applied = False
    application = None
    try:
        employee_profile = request.user.employeeprofile
        application = Application.objects.filter(
            job_posting=job,
            applicant=employee_profile
        ).first()
        user_applied = application is not None
    except EmployeeProfile.DoesNotExist:
        employee_profile = None

    # Get similar jobs (same location or type)
    similar_jobs = JobPosting.objects.filter(
        Q(location=job.location) | Q(job_type=job.job_type),
        status='OPEN'
    ).exclude(id=job.id).select_related('employer', 'location')[:4]

    context = {
        'job': job,
        'user_applied': user_applied,
        'application': application,
        'similar_jobs': similar_jobs,
        'has_profile': employee_profile is not None
    }

    return render(request, 'employees/job_detail.html', context)


@login_required
@user_passes_test(is_employee)
def apply_for_job(request, job_id):
    """Apply for a job posting"""
    job = get_object_or_404(JobPosting, id=job_id, status='OPEN')

    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.info(request, 'Please complete your employee profile before applying for jobs.')
        return redirect('employees:profile_setup')

    # Check if already applied
    if Application.objects.filter(job_posting=job, applicant=employee_profile).exists():
        messages.warning(request, 'You have already applied for this position.')
        return redirect('employees:job_detail', job_id=job.id)

    if request.method == 'POST':
        form = JobApplicationForm(
            request.POST,
            job_posting=job,
            employee_profile=employee_profile
        )
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('employees:job_detail', job_id=job.id)
    else:
        form = JobApplicationForm(
            job_posting=job,
            employee_profile=employee_profile
        )

    context = {
        'form': form,
        'job': job,
        'employee_profile': employee_profile
    }

    return render(request, 'employees/apply_for_job.html', context)


@login_required
@user_passes_test(is_employee)
def my_applications(request):
    """View user's job applications"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.info(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    applications = Application.objects.filter(
        applicant=employee_profile
    ).select_related('job_posting', 'job_posting__employer', 'job_posting__location').order_by('-created_at')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for filter tabs
    status_counts = {
        'all': Application.objects.filter(applicant=employee_profile).count(),
        'submitted': Application.objects.filter(applicant=employee_profile, status='SUBMITTED').count(),
        'reviewed': Application.objects.filter(applicant=employee_profile, status='REVIEWED').count(),
        'invited': Application.objects.filter(applicant=employee_profile, status='INVITED').count(),
        'hired': Application.objects.filter(applicant=employee_profile, status='HIRED').count(),
        'rejected': Application.objects.filter(applicant=employee_profile, status='REJECTED').count(),
    }

    context = {
        'page_obj': page_obj,
        'applications': page_obj,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'employee_profile': employee_profile
    }

    return render(request, 'employees/my_applications.html', context)


@login_required
@user_passes_test(is_employee)
def withdraw_application(request, application_id):
    """Withdraw a job application"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    application = get_object_or_404(
        Application,
        id=application_id,
        applicant=employee_profile
    )

    # Only allow withdrawal if status is SUBMITTED or REVIEWED
    if application.status not in ['SUBMITTED', 'REVIEWED']:
        messages.error(request, 'You cannot withdraw this application at this stage.')
        return redirect('employees:my_applications')

    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Your application has been withdrawn successfully.')
        return redirect('employees:my_applications')

    context = {
        'application': application
    }

    return render(request, 'employees/withdraw_application.html', context)


@login_required
@user_passes_test(is_employee)
def document_upload(request):
    """Upload or manage employee documents"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.info(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = profile
            document.save()

            document_type_display = document.get_document_type_display()
            messages.success(request, f'{document_type_display} uploaded successfully!')
            return redirect('employees:profile_view')
    else:
        form = DocumentUploadForm()

    # Get existing documents
    documents = Document.objects.filter(employee=profile).order_by('-created_at')

    context = {
        'form': form,
        'documents': documents,
        'profile': profile
    }

    return render(request, 'employees/document_upload.html', context)


@login_required
@user_passes_test(is_employee)
def document_delete(request, document_id):
    """Delete a document"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    document = get_object_or_404(Document, id=document_id, employee=profile)

    if request.method == 'POST':
        document_type = document.get_document_type_display()
        document.delete()
        messages.success(request, f'{document_type} deleted successfully.')
        return redirect('employees:document_upload')

    context = {
        'document': document
    }

    return render(request, 'employees/document_delete.html', context)