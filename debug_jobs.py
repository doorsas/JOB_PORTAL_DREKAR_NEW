#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_hr_portal.settings')
django.setup()

from employers.models import JobPosting

def debug_jobs():
    print("=== JOB DEBUG INFORMATION ===")
    print(f"Total jobs in database: {JobPosting.objects.count()}")

    # Check all job statuses
    print(f"\nJobs by status:")
    for status_choice in JobPosting.JobStatus.choices:
        status_value = status_choice[0]
        count = JobPosting.objects.filter(status=status_value).count()
        print(f"  {status_choice[1]} ({status_value}): {count}")

    # Show all jobs with their details
    print(f"\nAll jobs:")
    for job in JobPosting.objects.all():
        print(f"  ID: {job.id}")
        print(f"  Title: {job.title}")
        print(f"  Status: {job.status} ({job.get_status_display()})")
        print(f"  Employer: {job.employer}")
        print(f"  Created: {job.created_at}")
        print(f"  ---")

    # Check what the view would return
    open_jobs = JobPosting.objects.filter(status='OPEN')
    print(f"\nOPEN jobs (what the view should show): {open_jobs.count()}")
    for job in open_jobs:
        print(f"  - {job.title} at {job.employer}")

if __name__ == "__main__":
    debug_jobs()