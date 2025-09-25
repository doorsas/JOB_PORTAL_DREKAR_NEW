#!/bin/bash
# Ubuntu Lightsail Deployment Script for HR Portal

set -e  # Exit on any error

echo "🚀 Starting HR Portal deployment on Ubuntu..."

# Configuration
APP_NAME="hr-portal"
APP_USER="www-data"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="hr-portal"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    nginx \
    supervisor \
    git \
    curl \
    certbot \
    python3-certbot-nginx

# Create application directory
print_status "Setting up application directory..."
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# Create virtual environment
print_status "Creating Python virtual environment..."
cd $APP_DIR
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER venv/bin/pip install --upgrade pip

print_success "System setup complete!"

echo
echo "📋 Next steps to complete manually:"
echo "1. Upload your Django project to $APP_DIR"
echo "2. Install Python dependencies: sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt"
echo "3. Copy .env file with production settings"
echo "4. Run migrations: sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py migrate"
echo "5. Collect static files: sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py collectstatic --noinput"
echo "6. Create superuser: sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py createsuperuser"
echo "7. Set up systemd service"
echo "8. Configure Nginx"
echo "9. Set up SSL with Let's Encrypt"

print_success "Ubuntu server is ready for Django deployment!"