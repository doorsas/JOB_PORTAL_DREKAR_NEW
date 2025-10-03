#!/bin/bash
# Quick fix for weasyprint installation issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

APP_DIR="/var/www/hr-portal"
APP_USER="www-data"

print_status "Fixing weasyprint installation..."

# Stop the service first
print_status "Stopping hr-portal service..."
systemctl stop hr-portal

# Install additional system dependencies
print_status "Installing additional system dependencies..."
apt update
apt install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    shared-mime-info

# Go to app directory
cd $APP_DIR

# Update pip first
print_status "Upgrading pip..."
sudo -u $APP_USER venv/bin/pip install --upgrade pip

# Install weasyprint specifically with verbose output
print_status "Installing weasyprint..."
sudo -u $APP_USER venv/bin/pip install --no-cache-dir weasyprint==66.0 -v

# Verify installation
print_status "Verifying weasyprint installation..."
if sudo -u $APP_USER venv/bin/python -c "import weasyprint; print('WeasyPrint version:', weasyprint.__version__)"; then
    print_success "WeasyPrint installed successfully!"
else
    print_error "WeasyPrint installation failed!"

    # Try alternative installation method
    print_status "Trying alternative installation method..."
    sudo -u $APP_USER venv/bin/pip install --no-binary=weasyprint weasyprint==66.0

    # Test again
    if sudo -u $APP_USER venv/bin/python -c "import weasyprint; print('WeasyPrint version:', weasyprint.__version__)"; then
        print_success "WeasyPrint installed successfully with alternative method!"
    else
        print_error "WeasyPrint installation still failed. Trying to disable import temporarily..."

        # Comment out the problematic import temporarily
        print_status "Temporarily disabling weasyprint import..."
        sed -i 's/from weasyprint import HTML/# from weasyprint import HTML  # Temporarily disabled/' /var/www/hr-portal/core/utils.py
        sed -i 's/from .utils import generate_invoice_pdf/# from .utils import generate_invoice_pdf  # Temporarily disabled/' /var/www/hr-portal/core/services.py
        sed -i 's/from core.services import create_invoice_for_client/# from core.services import create_invoice_for_client  # Temporarily disabled/' /var/www/hr-portal/employers/services.py
        sed -i 's/from .services import generate_invoice_for_employer/# from .services import generate_invoice_for_employer  # Temporarily disabled/' /var/www/hr-portal/employers/admin.py

        print_warning "WeasyPrint imports have been temporarily disabled to allow the application to start."
        print_warning "PDF generation features will not work until WeasyPrint is properly installed."
    fi
fi

# Try to run migrations
print_status "Running database migrations..."
sudo -u $APP_USER venv/bin/python manage.py migrate

# Collect static files
print_status "Collecting static files..."
sudo -u $APP_USER venv/bin/python manage.py collectstatic --noinput

# Start the service
print_status "Starting hr-portal service..."
systemctl start hr-portal

# Check status
sleep 3
if systemctl is-active --quiet hr-portal; then
    print_success "HR Portal service is running!"
else
    print_error "Service failed to start. Check logs: journalctl -u hr-portal -f"
fi

print_success "Fix completed!"
echo
echo "📋 Next steps:"
echo "1. Check if the application loads: curl http://localhost:8000/"
echo "2. Create superuser: sudo -u www-data /var/www/hr-portal/venv/bin/python /var/www/hr-portal/manage.py createsuperuser"
echo "3. If WeasyPrint is still needed, try installing it manually later"