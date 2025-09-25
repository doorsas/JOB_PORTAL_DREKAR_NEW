from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, timedelta
import random

from employees.models import EmployeeProfile
from core.models import Address, Skill, Profession

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 10 test employees for testing purposes (no external dependencies)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of employees to create (default: 10)'
        )

    def handle(self, *args, **options):
        count = options['count']

        # Sample data
        first_names = [
            'Jonas', 'Petras', 'Antanas', 'Vytautas', 'Mindaugas',
            'Rasa', 'Ona', 'Jūratė', 'Dalia', 'Vida',
            'Andrius', 'Tomas', 'Gintaras', 'Saulius', 'Rolandas',
            'Indrė', 'Lina', 'Gintarė', 'Monika', 'Eglė'
        ]

        last_names = [
            'Petrauskas', 'Jankauskas', 'Kazlauskas', 'Vasiliauskas', 'Grigaliūnas',
            'Paulauskas', 'Žukauskas', 'Nausėda', 'Sabaliauskas', 'Balčiūnas',
            'Rimkus', 'Urbonas', 'Butkus', 'Klimaitis', 'Norkus',
            'Petrauskienė', 'Jankauskienė', 'Kazlauskienė', 'Vasiliūnienė', 'Paulauskienė'
        ]

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

        # Experience summaries
        experience_samples = [
            "Experienced professional with strong analytical skills and attention to detail.",
            "Team player with excellent communication skills and customer service experience.",
            "Results-oriented individual with proven track record in project management.",
            "Creative problem solver with experience in fast-paced environments.",
            "Detail-oriented professional with strong organizational skills.",
            "Customer-focused individual with excellent interpersonal skills.",
            "Motivated professional with leadership experience and team management skills.",
            "Technical professional with strong analytical and problem-solving abilities.",
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
                    # Generate names
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)

                    # Generate unique email and username
                    base_email = f"{first_name.lower()}.{last_name.lower()}{i+1}@testhr.com"
                    username = f"{first_name.lower()}{last_name.lower()}{i+1}"

                    # Ensure uniqueness
                    while User.objects.filter(email=base_email).exists():
                        base_email = f"{first_name.lower()}.{last_name.lower()}{i+random.randint(100, 999)}@testhr.com"

                    while User.objects.filter(username=username).exists():
                        username = f"{first_name.lower()}{last_name.lower()}{i+random.randint(100, 999)}"

                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=base_email,
                        password='testpass123',  # Same password for all test users
                        first_name=first_name,
                        last_name=last_name,
                        user_type='EMPLOYEE',
                        is_verified=random.choice([True, False])
                    )

                    # Generate birth date (18-65 years old)
                    today = date.today()
                    min_age = today - timedelta(days=65*365)
                    max_age = today - timedelta(days=18*365)
                    birth_date = min_age + timedelta(
                        days=random.randint(0, (max_age - min_age).days)
                    )

                    # Generate phone number
                    phone = f"+370 {random.randint(600, 699)} {random.randint(10000, 99999)}"

                    # Create employee profile
                    employee = EmployeeProfile.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        date_of_birth=birth_date,
                        address=random.choice(all_addresses) if all_addresses else None,
                        phone=phone,
                        nationality=random.choice([
                            'Lithuanian', 'Latvian', 'Estonian', 'Polish', 'German',
                            'Ukrainian', 'Russian', 'Belarusian', 'American', 'British'
                        ]),
                        experience_summary=random.choice(experience_samples) if random.choice([True, False]) else None,
                        expected_salary=random.randint(800, 5000) if random.choice([True, False]) else None,
                        current_status=random.choice(['AVAILABLE', 'EMPLOYED', 'ON_HOLD'])
                    )

                    # Add random skills (2-6 skills per employee)
                    if all_skills:
                        skill_count = min(random.randint(2, 6), len(all_skills))
                        selected_skills = random.sample(all_skills, skill_count)
                        employee.skills.set(selected_skills)

                    # Add random preferred professions (1-3 professions per employee)
                    if all_professions:
                        profession_count = min(random.randint(1, 3), len(all_professions))
                        selected_professions = random.sample(all_professions, profession_count)
                        employee.preferred_professions.set(selected_professions)

                    self.stdout.write(
                        self.style.SUCCESS(f'Created employee: {employee.full_name} ({user.email})')
                    )

                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {count} test employees!')
                )
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING('Login credentials for all test employees:')
                )
                self.stdout.write(
                    self.style.WARNING('Password: testpass123')
                )
                self.stdout.write('')
                self.stdout.write(
                    self.style.HTTP_INFO('Sample employee emails:')
                )

                # Show some sample emails
                sample_employees = EmployeeProfile.objects.filter(user__email__contains='testhr.com')[:5]
                for emp in sample_employees:
                    self.stdout.write(f'  - {emp.user.email}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test employees: {str(e)}')
            )
            raise e