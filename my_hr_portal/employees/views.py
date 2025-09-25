
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import EmployeeProfile, Document, Payslip, WorkSchedule, Timesheet, CV
from .forms import EmployeeProfileForm, JobSearchForm, JobApplicationForm, DocumentUploadForm, WorkScheduleForm, TimesheetForm, CVForm
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


@login_required
@user_passes_test(is_employee)
def payslip_detail(request, payslip_id):
    """View payslip details"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employees:dashboard')

    payslip = get_object_or_404(Payslip, id=payslip_id, employee=employee_profile)

    # Mark payslip as viewed
    if not payslip.viewed_at:
        payslip.viewed_at = timezone.now()
        if payslip.status == 'SENT':
            payslip.status = 'VIEWED'
        payslip.save()

    context = {
        'payslip': payslip,
    }
    return render(request, 'employees/payslip_detail.html', context)

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
    """Enhanced employee dashboard view with assignment tracking"""
    try:
        employee_profile = request.user.employeeprofile
        has_profile = True
    except EmployeeProfile.DoesNotExist:
        return render(request, 'employees/dashboard.html', {
            'user': request.user,
            'has_profile': False,
        })

    from django.utils import timezone
    from employers.models import Assignment
    today = timezone.now().date()

    # Assignment queries with time-based filtering
    current_assignments = Assignment.objects.filter(
        employee=employee_profile,
        status=Assignment.AssignmentStatus.ACTIVE,
        start_date__lte=today
    ).exclude(
        actual_end_date__lt=today
    ).select_related('employer', 'employment_contract')

    future_assignments = Assignment.objects.filter(
        employee=employee_profile,
        status=Assignment.AssignmentStatus.PENDING_START,
        start_date__gt=today
    ).select_related('employer', 'employment_contract')

    past_assignments = Assignment.objects.filter(
        employee=employee_profile,
        status__in=[Assignment.AssignmentStatus.COMPLETED, Assignment.AssignmentStatus.TERMINATED]
    ).select_related('employer', 'employment_contract')[:5]  # Latest 5

    # Check if CV is uploaded
    cv_document = Document.objects.filter(
        employee=employee_profile,
        document_type=Document.DocumentType.CV
    ).order_by('-created_at').first()

    # Statistics
    stats = {
        'total_applications': employee_profile.applications.count(),
        'pending_applications': employee_profile.applications.filter(status='SUBMITTED').count(),
        'total_assignments': Assignment.objects.filter(employee=employee_profile).count(),
        'active_assignments': current_assignments.count(),
        'completed_assignments': past_assignments.count(),
        'total_employers': Assignment.objects.filter(employee=employee_profile).values('employer').distinct().count(),
    }

    # Recent work schedules
    recent_schedules = WorkSchedule.objects.filter(
        employee=employee_profile,
        date__gte=today - timezone.timedelta(days=30)
    ).select_related('assignment__employer').order_by('-date')[:10]

    # Pending timesheets
    pending_timesheets = Timesheet.objects.filter(
        employee=employee_profile,
        status='PENDING'
    ).select_related('assignment__employer').order_by('-date')

    # Get CV information
    cv_document = Document.objects.filter(
        employee=employee_profile,
        document_type='CV'
    ).first()

    # Check if CV model exists
    try:
        cv = CV.objects.get(employee=employee_profile)
    except CV.DoesNotExist:
        cv = None

    context = {
        'user': request.user,
        'has_profile': has_profile,
        'profile': employee_profile,
        'has_cv': cv_document is not None,
        'cv': cv,
        'current_assignments': current_assignments,
        'future_assignments': future_assignments,
        'past_assignments': past_assignments,
        'recent_schedules': recent_schedules,
        'pending_timesheets': pending_timesheets,
        # Legacy stats for existing dashboard template
        'total_applications': stats['total_applications'],
        'pending_applications': stats['pending_applications'],
        'total_assignments': stats['total_assignments'],
        'active_assignments': stats['active_assignments'],
    }

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

    # Get the CV model instance
    try:
        cv = CV.objects.get(employee=profile)
    except CV.DoesNotExist:
        cv = None

    context = {
        'profile': profile,
        'cv_document': cv_document,
        'cv': cv
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

    # Debug: Show all jobs first
    all_jobs = JobPosting.objects.all()
    print(f"DEBUG: Total jobs in database: {all_jobs.count()}")
    for job in all_jobs:
        print(f"DEBUG: Job '{job.title}' has status '{job.status}'")

    # Filter for OPEN jobs
    jobs = JobPosting.objects.filter(status='OPEN').select_related('employer', 'location').prefetch_related('required_skills', 'required_qualifications')
    print(f"DEBUG: OPEN jobs found: {jobs.count()}")

    # Temporary: if no OPEN jobs, show all jobs for debugging
    if not jobs.exists():
        print("DEBUG: No OPEN jobs found, showing all jobs for debugging")
        jobs = JobPosting.objects.all().select_related('employer', 'location').prefetch_related('required_skills', 'required_qualifications')

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

    # Check if employee has uploaded CV
    has_cv = employee_profile.documents.filter(document_type='CV').exists()

    context = {
        'form': form,
        'job': job,
        'employee_profile': employee_profile,
        'has_cv': has_cv
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


@login_required
@user_passes_test(is_employee)
def schedules_view(request):
    """View employee work schedules"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.info(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    schedules = WorkSchedule.objects.filter(employee=profile).order_by('-date')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        schedules = schedules.filter(status=status_filter)

    # Pagination
    paginator = Paginator(schedules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'schedules': page_obj,
        'status_filter': status_filter,
        'profile': profile
    }

    return render(request, 'employees/schedules.html', context)


@login_required
@user_passes_test(is_employee)
def submit_timesheet(request, schedule_id):
    """Submit a timesheet for a work schedule"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    # Get the work schedule
    schedule = get_object_or_404(WorkSchedule, id=schedule_id, employee=profile)

    # Check if timesheet already exists
    existing_timesheet = Timesheet.objects.filter(work_schedule=schedule).first()

    if request.method == 'POST':
        form = TimesheetForm(request.POST, instance=existing_timesheet)
        if form.is_valid():
            timesheet = form.save(commit=False)
            timesheet.work_schedule = schedule
            timesheet.employee = profile
            timesheet.save()

            # Update schedule status to completed
            schedule.status = 'COMPLETED'
            schedule.save()

            messages.success(request, 'Timesheet submitted successfully.')
            return redirect('employees:schedules')
    else:
        form = TimesheetForm(instance=existing_timesheet)

    context = {
        'form': form,
        'schedule': schedule,
        'existing_timesheet': existing_timesheet
    }

    return render(request, 'employees/submit_timesheet.html', context)


@login_required
@user_passes_test(is_employee)
def my_assignments(request):
    """View all assignments for the employee"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    from employers.models import Assignment
    filter_status = request.GET.get('status', 'all')

    assignments = Assignment.objects.filter(employee=employee_profile).select_related('employer', 'employment_contract')

    if filter_status == 'current':
        assignments = assignments.filter(status=Assignment.AssignmentStatus.ACTIVE)
    elif filter_status == 'future':
        assignments = assignments.filter(status=Assignment.AssignmentStatus.PENDING_START)
    elif filter_status == 'past':
        assignments = assignments.filter(status__in=[Assignment.AssignmentStatus.COMPLETED, Assignment.AssignmentStatus.TERMINATED])

    assignments = assignments.order_by('-start_date')

    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'assignments': page_obj,
        'filter_status': filter_status,
        'employee_profile': employee_profile
    }

    return render(request, 'employees/my_assignments.html', context)


@login_required
@user_passes_test(is_employee)
def assignment_detail(request, assignment_id):
    """View assignment details for employee"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    from employers.models import Assignment
    assignment = get_object_or_404(Assignment, id=assignment_id, employee=employee_profile)

    # Get related work schedules and timesheets
    work_schedules = WorkSchedule.objects.filter(assignment=assignment).order_by('-date')[:10]
    timesheets = Timesheet.objects.filter(assignment=assignment).order_by('-date')[:10]
    payslips = assignment.payslips.order_by('-period_start_date')[:10]

    context = {
        'assignment': assignment,
        'work_schedules': work_schedules,
        'timesheets': timesheets,
        'payslips': payslips,
        'employee_profile': employee_profile,
    }

    return render(request, 'employees/assignment_detail.html', context)


@login_required
@user_passes_test(is_employee)
def cv_form(request):
    """Create or update employee CV"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    # Get or create CV
    cv, created = CV.objects.get_or_create(employee=employee_profile)

    if request.method == 'POST':
        form = CVForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your CV has been saved successfully!')
            return redirect('employees:cv_view')
    else:
        form = CVForm(instance=cv)

    context = {
        'form': form,
        'cv': cv,
        'employee_profile': employee_profile,
        'is_new': created
    }

    return render(request, 'employees/cv_form.html', context)


@login_required
@user_passes_test(is_employee)
def cv_view(request):
    """View employee CV"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Please complete your employee profile first.')
        return redirect('employees:profile_setup')

    try:
        cv = CV.objects.get(employee=employee_profile)
    except CV.DoesNotExist:
        messages.info(request, 'You haven\'t created your CV yet.')
        return redirect('employees:cv_form')

    context = {
        'cv': cv,
        'employee_profile': employee_profile
    }

    return render(request, 'employees/cv_view.html', context)


@login_required
@user_passes_test(is_employee)
def cv_download(request):
    """Download CV as PDF or redirect to attachment"""
    try:
        employee_profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('employees:profile_setup')

    try:
        cv = CV.objects.get(employee=employee_profile)
    except CV.DoesNotExist:
        messages.error(request, 'CV not found. Please create your CV first.')
        return redirect('employees:cv_form')

    # If there's an attachment, serve that
    if cv.attachment:
        from django.http import FileResponse
        import os

        file_path = cv.attachment.path
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=f"{employee_profile.full_name}_CV.{cv.attachment.name.split('.')[-1]}"
            )
            return response

    # Otherwise, render the CV as HTML for now (could be enhanced to generate PDF)
    messages.info(request, 'No CV attachment found. Showing CV details below.')
    return redirect('employees:cv_view')