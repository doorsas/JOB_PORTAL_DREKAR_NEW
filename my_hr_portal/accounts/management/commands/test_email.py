from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

User = get_user_model()


class Command(BaseCommand):
    help = 'Test email functionality in Django HR Portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['simple', 'password_reset', 'welcome'],
            default='simple',
            help='Type of test email to send'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for password reset test (required for password_reset type)'
        )

    def handle(self, *args, **options):
        email_type = options['type']
        test_email = options['email']

        self.stdout.write(f"[TEST] Testing {email_type} email...")
        self.stdout.write(f"[EMAIL] Target email: {test_email}")
        self.stdout.write(f"[BACKEND] Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write("-" * 60)

        try:
            if email_type == 'simple':
                self.send_simple_test_email(test_email)
            elif email_type == 'password_reset':
                username = options.get('username')
                if not username:
                    raise CommandError("Username is required for password_reset test. Use --username=your_username")
                self.send_password_reset_email(username, test_email)
            elif email_type == 'welcome':
                self.send_welcome_email(test_email)

            self.stdout.write(
                self.style.SUCCESS("[SUCCESS] Test email sent successfully!")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] Failed to send email: {str(e)}")
            )

    def send_simple_test_email(self, email):
        """Send a simple test email"""
        subject = "[TEST] Email from HR Portal"
        message = """
Hello!

This is a test email from the HR Portal development server.

If you're seeing this email, it means:
- Django email configuration is working
- Email backend is properly set up
- SMTP connection is successful

Test Details:
- Sent from: HR Portal Development Server
- Email Backend: {backend}
- Time: {time}

Best regards,
HR Portal Development Team
        """.format(
            backend=settings.EMAIL_BACKEND,
            time=self.get_current_time()
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

    def send_password_reset_email(self, username, email):
        """Send a password reset email"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Create a temporary user for testing
            user = User.objects.create_user(
                username=username,
                email=email,
                password='temppass123'
            )
            self.stdout.write(f"[INFO] Created temporary user: {username}")

        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Get current site
        try:
            current_site = Site.objects.get_current()
            domain = current_site.domain
        except:
            domain = 'localhost:8080'

        # Email context
        context = {
            'email': user.email,
            'domain': domain,
            'site_name': 'HR Portal',
            'uid': uid,
            'user': user,
            'token': token,
            'protocol': 'http',
        }

        # Render email content
        subject = "[PASSWORD RESET] HR Portal Password Reset"
        email_template = 'accounts/password_reset_email.html'

        try:
            email_content = render_to_string(email_template, context)
        except:
            # Fallback to simple text if template fails
            email_content = f"""
Password Reset Request

Hello {user.username},

You requested a password reset for your HR Portal account.

Reset link: http://{domain}/accounts/reset/{uid}/{token}/

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
HR Portal Team
            """

        send_mail(
            subject=subject,
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=email_content
        )

        self.stdout.write(f"[SENT] Password reset email sent for user: {username}")
        self.stdout.write(f"[URL] Reset URL: http://{domain}/accounts/reset/{uid}/{token}/")

    def send_welcome_email(self, email):
        """Send a welcome email"""
        subject = "[WELCOME] Welcome to HR Portal!"
        message = f"""
Welcome to HR Portal!

Thank you for joining our platform. We're excited to have you on board!

What you can do:
- Browse job opportunities
- Manage your profile
- Apply for positions
- Track your applications

Getting Started:
1. Complete your profile
2. Upload your CV
3. Start applying for jobs

If you have any questions, don't hesitate to contact our support team.

Welcome aboard!

The HR Portal Team

---
This email was sent to: {email}
Time: {self.get_current_time()}
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

    def get_current_time(self):
        """Get current formatted time"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")