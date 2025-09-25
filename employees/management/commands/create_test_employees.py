from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
from datetime import date, timedelta
import random

from employees.models import EmployeeProfile
from core.models import Address, Skill, Profession

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 10 test employees for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of employees to create (default: 10)'
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']

        # Skills data
        skills_data = [
            'Communication', 'Teamwork', 'Problem Solving', 'Time Management',
            'Leadership', 'Customer Service', 'Computer Skills', 'Microsoft Office',
            'Data Analysis', 'Project Management', 'Sales', 'Marketing',
            'Accounting', 'Programming', 'Database Management', 'Graphic Design',
            'Writing', 'Research', 'Languages', 'Social Media'
        ]

        # Professions data
        professions_data = [
            'Software Developer', 'Customer Service Representative', 'Sales Associate',
            'Administrative Assistant', 'Marketing Specialist', 'Data Analyst',
            'Graphic Designer', 'Accountant', 'Project Manager', 'HR Specialist',
            'Content Writer', 'Social Media Manager', 'Warehouse Worker',
            'Security Guard', 'Receptionist'
        ]

        # Sample addresses data
        addresses_data = [
            {'street_address': 'Gedimino pr. 15', 'city': 'Vilnius', 'postal_code': '01103', 'country': 'Lithuania'},
            {'street_address': 'Laisvės al. 25', 'city': 'Kaunas', 'postal_code': '44249', 'country': 'Lithuania'},
            {'street_address': 'Maironio g. 8', 'city': 'Klaipėda', 'postal_code': '92251', 'country': 'Lithuania'},
            {'street_address': 'Savanorių pr. 12', 'city': 'Šiauliai', 'postal_code': '76285', 'country': 'Lithuania'},
            {'street_address': 'Vytauto g. 30', 'city': 'Panevėžys', 'postal_code': '35200', 'country': 'Lithuania'},
        ]

        try:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS('Creating sample data...'))

                # Create skills if they don't exist
                for skill_name in skills_data:
                    Skill.objects.get_or_create(
                        name=skill_name,
                        defaults={'category': 'General'}
                    )

                # Create professions if they don't exist
                for profession_name in professions_data:
                    Profession.objects.get_or_create(
                        name=profession_name,
                        defaults={'description': f'{profession_name} profession'}
                    )

                # Create addresses if they don't exist
                for address_data in addresses_data:
                    Address.objects.get_or_create(**address_data)

                # Get all available data
                all_skills = list(Skill.objects.all())
                all_professions = list(Profession.objects.all())
                all_addresses = list(Address.objects.all())

                self.stdout.write(self.style.SUCCESS(f'Creating {count} test employees...'))

                for i in range(count):
                    # Generate unique email
                    email = fake.unique.email()
                    while User.objects.filter(email=email).exists():
                        email = fake.unique.email()

                    # Create user
                    user = User.objects.create_user(
                        username=fake.unique.user_name(),
                        email=email,
                        password='testpass123',  # Same password for all test users
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        user_type='EMPLOYEE',
                        is_verified=random.choice([True, False])
                    )

                    # Create employee profile
                    employee = EmployeeProfile.objects.create(
                        user=user,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=65),
                        address=random.choice(all_addresses) if all_addresses else None,
                        phone=fake.phone_number()[:20],  # Ensure it fits in the field
                        nationality=random.choice([
                            'Lithuanian', 'Latvian', 'Estonian', 'Polish', 'German',
                            'Ukrainian', 'Russian', 'Belarusian', 'American', 'British'
                        ]),
                        experience_summary=fake.text(max_nb_chars=500) if random.choice([True, False]) else None,
                        expected_salary=random.randint(800, 5000) if random.choice([True, False]) else None,
                        current_status=random.choice(['AVAILABLE', 'EMPLOYED', 'ON_HOLD'])
                    )

                    # Add random skills (2-6 skills per employee)
                    if all_skills:
                        selected_skills = random.sample(all_skills, min(random.randint(2, 6), len(all_skills)))
                        employee.skills.set(selected_skills)

                    # Add random preferred professions (1-3 professions per employee)
                    if all_professions:
                        selected_professions = random.sample(all_professions, min(random.randint(1, 3), len(all_professions)))
                        employee.preferred_professions.set(selected_professions)

                    self.stdout.write(
                        self.style.SUCCESS(f'Created employee: {employee.full_name} ({user.email})')
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {count} test employees!')
                )
                self.stdout.write(
                    self.style.WARNING('All test employees have password: testpass123')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test employees: {str(e)}')
            )
            raise e