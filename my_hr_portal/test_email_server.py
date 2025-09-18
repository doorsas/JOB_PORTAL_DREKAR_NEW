#!/usr/bin/env python3
"""
Simple SMTP Test Server for Django Development

This script runs a simple SMTP server that prints all received emails to the console.
Perfect for testing Django's email functionality during development.

Usage:
1. Run this script: python test_email_server.py
2. Update Django settings to use SMTP backend pointing to localhost:1025
3. Test your Django app's email functionality

The server will print all received emails with full headers and content.
"""

import smtpd
import smtplib
import asyncore
import threading
import time
from datetime import datetime


class TestSMTPServer(smtpd.SMTPServer):
    """Custom SMTP Server that prints emails to console"""

    def __init__(self, localaddr, remoteaddr):
        print(f"🚀 Starting Test SMTP Server on {localaddr[0]}:{localaddr[1]}")
        print(f"📧 All emails will be printed to this console")
        print(f"⏰ Server started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        super().__init__(localaddr, remoteaddr)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Process incoming email and print to console"""
        print("\n" + "=" * 80)
        print(f"📨 NEW EMAIL RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        print(f"🔗 Connection from: {peer[0]}:{peer[1]}")
        print(f"📤 From: {mailfrom}")
        print(f"📥 To: {', '.join(rcpttos)}")
        print("-" * 80)
        print("📄 EMAIL CONTENT:")
        print("-" * 80)

        # Decode the email data if it's bytes
        if isinstance(data, bytes):
            try:
                email_content = data.decode('utf-8')
            except UnicodeDecodeError:
                email_content = data.decode('utf-8', errors='replace')
        else:
            email_content = data

        print(email_content)
        print("=" * 80)
        print("✅ Email processed successfully!")
        print("=" * 80 + "\n")


def run_server(host='localhost', port=1025):
    """Run the test SMTP server"""
    try:
        server = TestSMTPServer((host, port), None)
        print(f"🟢 Server is running and ready to receive emails!")
        print(f"🔧 To use with Django, update your settings.py:")
        print(f"   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'")
        print(f"   EMAIL_HOST = '{host}'")
        print(f"   EMAIL_PORT = {port}")
        print(f"   EMAIL_HOST_USER = ''")
        print(f"   EMAIL_HOST_PASSWORD = ''")
        print(f"   EMAIL_USE_TLS = False")
        print("=" * 80)
        print("⏹️  Press Ctrl+C to stop the server")
        print("=" * 80)

        # Start the server loop
        asyncore.loop()

    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("👋 Goodbye!")
    except OSError as e:
        if e.errno == 10048:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Run a test SMTP server for Django development')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=1025, help='Port to bind to (default: 1025)')

    args = parser.parse_args()

    print("🧪 Django Test Email Server")
    print("=" * 40)

    run_server(args.host, args.port)