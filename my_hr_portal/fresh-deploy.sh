#!/bin/bash
# Fresh deployment script for empty HR Portal directory
# Use this when the server directory is empty or needs complete setup

set -e  # Exit on any error

# Configuration
APP_NAME="hr-portal"
APP_USER="www-data"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="hr-portal"
REPO_URL="https://github.com/doorsas/JOB_PORTAL_DREKAR_NEW.git"

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

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Starting fresh HR Portal deployment..."

# Install system dependencies for weasyprint
print_status "Installing system dependencies for PDF generation..."
apt update
apt install -y \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

# Stop service if it exists
print_status "Stopping $SERVICE_NAME service (if running)..."
systemctl stop $SERVICE_NAME 2>/dev/null || print_warning "Service not running or doesn't exist"

# Ensure app directory exists and is empty
print_status "Preparing application directory..."
cd /var/www

# Remove existing content if any
if [ -d "$APP_DIR" ] && [ "$(ls -A $APP_DIR)" ]; then
    print_warning "Directory not empty. Backing up existing content..."
    mv $APP_DIR "${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# Remove directory if it exists to ensure clean clone
rm -rf $APP_DIR

# Clone the repository as root first, then change ownership
print_status "Cloning repository from GitHub..."
git clone $REPO_URL $APP_DIR

# Change ownership to www-data
print_status "Setting ownership to $APP_USER..."
chown -R $APP_USER:$APP_USER $APP_DIR

# Change to app directory
cd $APP_DIR

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
chown -R $APP_USER:$APP_USER venv

# Upgrade pip
print_status "Upgrading pip..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
if [ -f "$APP_DIR/my_hr_portal/requirements.txt" ]; then
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/my_hr_portal/requirements.txt
else
    print_error "requirements.txt not found at $APP_DIR/my_hr_portal/requirements.txt"
    exit 1
fi

# Set up directories
print_status "Creating necessary directories..."
sudo -u $APP_USER mkdir -p $APP_DIR/my_hr_portal/logs
sudo -u $APP_USER mkdir -p $APP_DIR/my_hr_portal/media
sudo -u $APP_USER mkdir -p $APP_DIR/my_hr_portal/staticfiles

# Copy environment file if it exists in the repo or restore from backup
if [ -f ~/hr-portal-backup.env ]; then
    print_status "Restoring .env from backup..."
    cp ~/hr-portal-backup.env $APP_DIR/my_hr_portal/.env
    chown $APP_USER:$APP_USER $APP_DIR/my_hr_portal/.env
elif [ -f "$APP_DIR/my_hr_portal/.env.example" ]; then
    print_status "Setting up environment file from example..."
    sudo -u $APP_USER cp $APP_DIR/my_hr_portal/.env.example $APP_DIR/my_hr_portal/.env
    print_warning "Please update .env file with your production settings!"
else
    print_warning "No .env file found. Please create one at $APP_DIR/my_hr_portal/.env"
fi

# Restore database from backup if exists
if [ -f ~/hr-portal-backup-db.sqlite3 ]; then
    print_status "Restoring database from backup..."
    cp ~/hr-portal-backup-db.sqlite3 $APP_DIR/my_hr_portal/db.sqlite3
    chown $APP_USER:$APP_USER $APP_DIR/my_hr_portal/db.sqlite3
fi

# Run database migrations
print_status "Running database migrations..."
cd $APP_DIR/my_hr_portal
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py makemigrations
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py migrate

# Create cache table
print_status "Creating cache table..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py createcachetable

# Collect static files
print_status "Collecting static files..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py collectstatic --noinput

# Set proper permissions
print_status "Setting proper permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 644 $APP_DIR/staticfiles/ 2>/dev/null || true

# Create systemd service file if it doesn't exist
if [ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    print_status "Creating systemd service file..."
    cp $APP_DIR/my_hr_portal/hr-portal.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
fi

# Create Nginx configuration if it doesn't exist
if [ ! -f "/etc/nginx/sites-available/$APP_NAME" ]; then
    print_status "Setting up Nginx configuration..."
    cp $APP_DIR/my_hr_portal/nginx-hr-portal.conf /etc/nginx/sites-available/$APP_NAME
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
fi

# Start services
print_status "Starting services..."
systemctl start $SERVICE_NAME
systemctl reload nginx

# Wait for services to start
sleep 5

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "$SERVICE_NAME is running"
else
    print_error "$SERVICE_NAME failed to start"
    print_error "Check logs: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# Health check
print_status "Performing health check..."
sleep 5
if curl -f -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    print_success "Health check passed"
else
    print_warning "Health check failed - application may still be starting"
fi

print_success "✅ Fresh deployment completed successfully!"
print_success "🌐 Your HR Portal is now deployed!"

echo
echo "📋 Post-deployment checklist:"
echo "1. Update .env file with production settings: $APP_DIR/my_hr_portal/.env"
echo "2. Create superuser: cd $APP_DIR/my_hr_portal && sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py createsuperuser"
echo "3. Test the application in your browser"
echo "4. Set up SSL certificate with Let's Encrypt"
echo "5. Configure domain name in Nginx if needed"

echo
echo "📊 Useful commands:"
echo "- Check service status: systemctl status $SERVICE_NAME"
echo "- View logs: journalctl -u $SERVICE_NAME -f"
echo "- Restart service: systemctl restart $SERVICE_NAME"

# Display service status
echo
print_status "Current service status:"
systemctl status $SERVICE_NAME --no-pager -l