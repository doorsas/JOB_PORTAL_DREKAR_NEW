from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
import json
from django.core.paginator import Paginator
from .models import JobPosting, EmployerProfile, Application, Assignment
from .forms import JobPostingForm, EmployerProfileForm
from django.db.models import Sum, F
from core.models import Invoice, Contract, ContractTemplate
from django.contrib.contenttypes.models import ContentType
from core.services import create_invoice_for_client
from datetime import date, timedelta


def is_employer(user):
    return user.is_authenticated and user.user_type == 'EMPLOYER'


@login_required
@user_passes_test(is_employer)
def dashboard(request):
    """Enhanced employer dashboard view with assignment tracking"""
    try:
        employer_profile = request.user.employerprofile
        has_profile = True
    except EmployerProfile.DoesNotExist:
        return render(request, 'employers/dashboard.html', {
            'user': request.user,
            'has_profile': False,
        })

    from django.utils import timezone
    from employees.models import Timesheet
    today = timezone.now().date()

    # Assignment queries
    current_assignments = Assignment.objects.filter(
        employer=employer_profile,
        status=Assignment.AssignmentStatus.ACTIVE,
        start_date__lte=today
    ).exclude(
        actual_end_date__lt=today
    ).select_related('employee', 'employment_contract')

    upcoming_assignments = Assignment.objects.filter(
        employer=employer_profile,
        status=Assignment.AssignmentStatus.PENDING_START,
        start_date__gt=today,
        start_date__lte=today + timezone.timedelta(days=30)
    ).select_related('employee')

    past_assignments = Assignment.objects.filter(
        employer=employer_profile,
        status__in=[Assignment.AssignmentStatus.COMPLETED, Assignment.AssignmentStatus.TERMINATED]
    ).select_related('employee')[:5]

    # Statistics
    stats = {
        'total_job_postings': employer_profile.job_postings.count(),
        'active_job_postings': employer_profile.job_postings.filter(status=JobPosting.JobStatus.OPEN).count(),
        'total_assignments': Assignment.objects.filter(employer=employer_profile).count(),
        'active_employees': current_assignments.count(),
        'total_employees': Assignment.objects.filter(employer=employer_profile).values('employee').distinct().count(),
    }

    # Recent timesheets needing approval
    pending_timesheets = Timesheet.objects.filter(
        assignment__employer=employer_profile,
        status='PENDING'
    ).select_related('employee', 'assignment').order_by('-submitted_at')[:10]

    # Add recent job postings (last 5)
    recent_jobs = employer_profile.job_postings.order_by('-created_at')[:5]
    for job in recent_jobs:
        job.applications_count = job.applications.count()

    context = {
        'user': request.user,
        'has_profile': has_profile,
        'profile': employer_profile,
        'current_assignments': current_assignments,
        'upcoming_assignments': upcoming_assignments,
        'past_assignments': past_assignments,
        'pending_timesheets': pending_timesheets,
        'recent_job_postings': recent_jobs,
        # Legacy stats for existing dashboard template
        'total_job_postings': stats['total_job_postings'],
        'active_job_postings': stats['active_job_postings'],
        'total_assignments': stats['total_assignments'],
        'active_assignments': stats['active_employees'],
    }

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
    job_postings = JobPosting.objects.filter(employer=employer_profile).order_by('-created_at')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        job_postings = job_postings.filter(status=JobPosting.JobStatus.OPEN)
    elif status_filter == 'inactive':
        job_postings = job_postings.filter(status__in=[JobPosting.JobStatus.DRAFT, JobPosting.JobStatus.CLOSED, JobPosting.JobStatus.FILLED])

    # Pagination
    paginator = Paginator(job_postings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add application counts for each job posting
    for job in page_obj:
        job.applications_count = job.applications.count()
        job.new_applications_count = job.applications.filter(status=Application.ApplicationStatus.SUBMITTED).count()

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

            if job_posting.status == JobPosting.JobStatus.OPEN:
                job_posting.status = JobPosting.JobStatus.CLOSED
            else:
                job_posting.status = JobPosting.JobStatus.OPEN
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
    applications = job_posting.applications.all().order_by('-created_at')

    # Pagination for applications
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    applications_page = paginator.get_page(page_number)

    context = {
        'job_posting': job_posting,
        'applications': applications_page,
        'applications_count': applications.count(),
        'new_applications_count': applications.filter(status=Application.ApplicationStatus.SUBMITTED).count(),
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
    ).select_related('job_posting', 'applicant', 'applicant__user').order_by('-created_at')

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
        'submitted': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.SUBMITTED).count(),
        'reviewed': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.REVIEWED).count(),
        'invited': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.INVITED).count(),
        'hired': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.HIRED).count(),
        'reserved': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.RESERVED).count(),
        'rejected': Application.objects.filter(job_posting__employer=employer_profile, status=Application.ApplicationStatus.REJECTED).count(),
    }

    # Get job postings for filter dropdown
    job_postings = JobPosting.objects.filter(employer=employer_profile).order_by('-created_at')

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
        # Get all valid status choices
        valid_statuses = [choice[0] for choice in Application.ApplicationStatus.choices]
        if new_status in valid_statuses:
            application.status = new_status
            application.save()

            status_display = application.get_status_display()
            messages.success(request, f'Application status updated to {status_display}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('employers:application_detail', application_id=application.id)


@login_required
@user_passes_test(is_employer)
def update_application_status_ajax(request, application_id):
    """Update application status via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employer profile not found'})

    try:
        application = get_object_or_404(
            Application,
            id=application_id,
            job_posting__employer=employer_profile
        )
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'})

    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')

        # Validate status
        valid_statuses = [choice[0] for choice in Application.ApplicationStatus.choices]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'})

        # Update application
        old_status = application.status
        application.status = new_status

        # Update notes if provided
        if notes:
            if application.notes:
                application.notes += f"\n\n[{request.user.get_full_name() or request.user.username}]: {notes}"
            else:
                application.notes = f"[{request.user.get_full_name() or request.user.username}]: {notes}"

        application.save()

        return JsonResponse({
            'success': True,
            'status': new_status,
            'status_display': application.get_status_display(),
            'old_status': old_status,
            'message': f'Application status updated from {dict(Application.ApplicationStatus.choices)[old_status]} to {application.get_status_display()}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


@login_required
@user_passes_test(is_employer)
def assignments_list(request):
    """View and manage employee assignments"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    assignments = Assignment.objects.filter(employer=employer_profile).select_related(
        'employee', 'job_posting', 'employment_contract'
    ).order_by('-start_date')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    # Pagination
    paginator = Paginator(assignments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for filter tabs
    status_counts = {
        'all': Assignment.objects.filter(employer=employer_profile).count(),
        'pending_start': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.PENDING_START).count(),
        'active': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.ACTIVE).count(),
        'completed': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.COMPLETED).count(),
        'terminated': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.TERMINATED).count(),
        'paused': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.PAUSED).count(),
        'cancelled': Assignment.objects.filter(employer=employer_profile, status=Assignment.AssignmentStatus.CANCELLED).count(),
    }

    context = {
        'page_obj': page_obj,
        'assignments': page_obj,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/assignments.html', context)


@login_required
@user_passes_test(is_employer)
def assignment_detail(request, assignment_id):
    """View detailed assignment information"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Employer profile not found.')
        return redirect('employers:profile_setup')

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        employer=employer_profile
    )

    context = {
        'assignment': assignment,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/assignment_detail.html', context)


@login_required
@user_passes_test(is_employer)
def invoices_list(request):
    """View and manage invoices for the employer"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.info(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    # Get the ContentType for EmployerProfile
    employer_content_type = ContentType.objects.get_for_model(EmployerProfile)

    # Get invoices for this employer with calculated total amounts
    invoices = Invoice.objects.filter(
        client_content_type=employer_content_type,
        client_object_id=employer_profile.id
    ).annotate(
        total_amount_calculated=Sum(F('line_items__quantity') * F('line_items__unit_price'))
    ).order_by('-issue_date')

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    # Pagination
    paginator = Paginator(invoices, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for filter tabs
    all_invoices = Invoice.objects.filter(
        client_content_type=employer_content_type,
        client_object_id=employer_profile.id
    )
    status_counts = {
        'all': all_invoices.count(),
        'pending': all_invoices.filter(status=Invoice.InvoiceStatus.PENDING).count(),
        'paid': all_invoices.filter(status=Invoice.InvoiceStatus.PAID).count(),
        'overdue': all_invoices.filter(status=Invoice.InvoiceStatus.OVERDUE).count(),
        'canceled': all_invoices.filter(status=Invoice.InvoiceStatus.CANCELED).count(),
    }

    context = {
        'page_obj': page_obj,
        'invoices': page_obj,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/invoices.html', context)


@login_required
@user_passes_test(is_employer)
def invoice_detail(request, invoice_id):
    """View detailed invoice information"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Employer profile not found.')
        return redirect('employers:profile_setup')

    # Get the ContentType for EmployerProfile
    employer_content_type = ContentType.objects.get_for_model(EmployerProfile)

    # Get the invoice with calculated total amount
    invoice = get_object_or_404(
        Invoice.objects.annotate(
            total_amount_calculated=Sum(F('line_items__quantity') * F('line_items__unit_price'))
        ),
        id=invoice_id,
        client_content_type=employer_content_type,
        client_object_id=employer_profile.id
    )

    # Get line items for the invoice
    line_items = invoice.line_items.all()

    # Get payments for the invoice
    payments = invoice.payments.all().order_by('-payment_date')

    # Calculate totals
    total_paid = payments.filter(status='SUCCESS').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    remaining_balance = (invoice.total_amount_calculated or 0) - total_paid

    context = {
        'invoice': invoice,
        'line_items': line_items,
        'payments': payments,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/invoice_detail.html', context)


@login_required
@user_passes_test(is_employer)
def create_invoice(request):
    """Create a new invoice using the service function"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Employer profile not found.')
        return redirect('employers:profile_setup')

    if request.method == 'POST':
        try:
            # Get form data
            issue_date = request.POST.get('issue_date', date.today())
            due_date_str = request.POST.get('due_date')

            # Parse due date or default to 30 days from issue
            if due_date_str:
                due_date = date.fromisoformat(due_date_str)
            else:
                due_date = date.today() + timedelta(days=30)

            # Get line items from form
            line_items_data = []
            item_count = int(request.POST.get('item_count', 0))

            for i in range(item_count):
                description = request.POST.get(f'item_{i}_description', '').strip()
                quantity = request.POST.get(f'item_{i}_quantity', '0')
                unit_price = request.POST.get(f'item_{i}_unit_price', '0')

                if description and quantity and unit_price:
                    try:
                        line_items_data.append({
                            'description': description,
                            'quantity': float(quantity),
                            'unit_price': float(unit_price)
                        })
                    except ValueError:
                        messages.error(request, f'Invalid quantity or price for item: {description}')
                        return render(request, 'employers/create_invoice.html', {'employer_profile': employer_profile})

            if not line_items_data:
                messages.error(request, 'Please add at least one line item.')
                return render(request, 'employers/create_invoice.html', {'employer_profile': employer_profile})

            # Create invoice using the service function
            invoice = create_invoice_for_client(
                client_object=employer_profile,
                issue_date=issue_date,
                due_date=due_date,
                line_items_data=line_items_data
            )

            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('employers:invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')
            return render(request, 'employers/create_invoice.html', {'employer_profile': employer_profile})

    context = {
        'employer_profile': employer_profile,
        'today': date.today(),
        'default_due_date': date.today() + timedelta(days=30)
    }

    return render(request, 'employers/create_invoice.html', context)


# ===================================================
# CONTRACT MANAGEMENT VIEWS
# ===================================================

@login_required
@user_passes_test(is_employer)
def contracts_list(request):
    """List all contracts for the employer"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    # Get filter parameters
    status_filter = request.GET.get('status', '')

    # Filter contracts
    contracts = Contract.objects.filter(employer_profile=employer_profile).order_by('-created_at')

    if status_filter:
        contracts = contracts.filter(status=status_filter)

    # Pagination
    paginator = Paginator(contracts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for filter tabs
    status_counts = {
        'all': Contract.objects.filter(employer_profile=employer_profile).count(),
        'draft': Contract.objects.filter(employer_profile=employer_profile, status='DRAFT').count(),
        'pending': Contract.objects.filter(employer_profile=employer_profile, status='PENDING_SIGNATURE').count(),
        'active': Contract.objects.filter(employer_profile=employer_profile, status='ACTIVE').count(),
        'expired': Contract.objects.filter(employer_profile=employer_profile, status='EXPIRED').count(),
        'cancelled': Contract.objects.filter(employer_profile=employer_profile, status='CANCELLED').count(),
    }

    context = {
        'page_obj': page_obj,
        'contracts': page_obj,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/contracts.html', context)


@login_required
@user_passes_test(is_employer)
def contract_detail(request, contract_id):
    """View contract details"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    contract = get_object_or_404(Contract, id=contract_id, employer_profile=employer_profile)

    context = {
        'contract': contract,
        'employer_profile': employer_profile
    }

    return render(request, 'employers/contract_detail.html', context)


@login_required
@user_passes_test(is_employer)
def create_contract(request):
    """Create a new contract"""
    try:
        employer_profile = request.user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Please complete your employer profile first.')
        return redirect('employers:profile_setup')

    if request.method == 'POST':
        try:
            contract_type = request.POST.get('contract_type')
            template_id = request.POST.get('template_id')
            effective_date = request.POST.get('effective_date')
            expiry_date = request.POST.get('expiry_date')

            # Validate required fields
            if not contract_type or not effective_date:
                messages.error(request, 'Contract type and effective date are required.')
                return render(request, 'employers/create_contract.html', {
                    'employer_profile': employer_profile,
                    'templates': ContractTemplate.objects.filter(is_active=True),
                    'contract_types': Contract.ContractType.choices
                })

            # Get template if provided
            template = None
            if template_id:
                template = get_object_or_404(ContractTemplate, id=template_id, is_active=True)

            # Create contract
            contract = Contract.objects.create(
                contract_type=contract_type,
                employer_profile=employer_profile,
                template_used=template,
                effective_date=effective_date,
                expiry_date=expiry_date if expiry_date else None,
                status=Contract.ContractStatus.DRAFT
            )

            messages.success(request, f'Contract created successfully!')
            return redirect('employers:contract_detail', contract_id=contract.id)

        except Exception as e:
            messages.error(request, f'Error creating contract: {str(e)}')

    # Get available templates
    templates = ContractTemplate.objects.filter(is_active=True)

    context = {
        'employer_profile': employer_profile,
        'templates': templates,
        'contract_types': Contract.ContractType.choices,
        'today': date.today()
    }

    return render(request, 'employers/create_contract.html', context)


@login_required
@user_passes_test(is_employer)
def update_contract_status(request, contract_id):
    """Update contract status via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        employer_profile = request.user.employerprofile
        contract = get_object_or_404(Contract, id=contract_id, employer_profile=employer_profile)

        data = json.loads(request.body)
        new_status = data.get('status')

        if new_status not in dict(Contract.ContractStatus.choices):
            return JsonResponse({'success': False, 'error': 'Invalid status'})

        contract.status = new_status

        # Set signed date if moving to active
        if new_status == Contract.ContractStatus.ACTIVE and not contract.signed_date:
            contract.signed_date = date.today()

        contract.save()

        return JsonResponse({
            'success': True,
            'new_status': contract.get_status_display(),
            'status_class': f'status-{new_status.lower()}'
        })

    except EmployerProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employer profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})