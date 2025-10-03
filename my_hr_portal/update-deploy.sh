#!/bin/bash
# HR Portal Update Deployment Script for Ubuntu
# This script safely updates your deployed application

set -e  # Exit on any error

# Configuration
APP_NAME="hr-portal"
APP_USER="www-data"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="hr-portal"
BACKUP_DIR="/var/backups/$APP_NAME"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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

print_status "Starting HR Portal update deployment..."

# Create backup directory
print_status "Creating backup directory..."
mkdir -p $BACKUP_DIR

# Backup current application
print_status "Backing up current application..."
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "/var/www" "$APP_NAME" || {
    print_error "Backup failed"
    exit 1
}
print_success "Backup created: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# Stop the service
print_status "Stopping $SERVICE_NAME service..."
systemctl stop $SERVICE_NAME

# Update source code (assumes you're using git)
print_status "Updating source code..."
cd $APP_DIR
if [ -d ".git" ]; then
    # Git-based update
    sudo -u $APP_USER git fetch origin
    sudo -u $APP_USER git pull origin master
    print_success "Code updated from Git repository"
else
    print_warning "No Git repository found. Please manually copy your updated files to $APP_DIR"
    print_warning "Press any key to continue after copying files..."
    read -n 1
fi

# Update virtual environment
print_status "Updating Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt --upgrade

# Run database migrations
print_status "Running database migrations..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py makemigrations
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py migrate

# Collect static files
print_status "Collecting static files..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py collectstatic --noinput

# Update cache table (if using database cache)
print_status "Updating cache table..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py createcachetable

# Clear any Django cache
print_status "Clearing Django cache..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Set proper permissions
print_status "Setting proper permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 644 $APP_DIR/staticfiles/

# Restart services
print_status "Restarting services..."
systemctl start $SERVICE_NAME
systemctl reload nginx

# Wait a moment for services to start
sleep 3

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "$SERVICE_NAME is running"
else
    print_error "$SERVICE_NAME failed to start"
    print_warning "Rolling back to previous version..."

    # Rollback
    systemctl stop $SERVICE_NAME
    cd /var/www
    rm -rf $APP_NAME
    tar -xzf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    chown -R $APP_USER:$APP_USER $APP_NAME
    systemctl start $SERVICE_NAME

    print_error "Rollback completed. Check logs for errors."
    exit 1
fi

# Health check
print_status "Performing health check..."
sleep 5
if curl -f -s http://127.0.0.1:8000/health/ > /dev/null 2>&1; then
    print_success "Health check passed"
else
    print_warning "Health check failed, but service is running"
fi

# Cleanup old backups (keep last 5)
print_status "Cleaning up old backups..."
cd $BACKUP_DIR
ls -t backup_*.tar.gz | tail -n +6 | xargs -r rm

print_success "✅ Deployment completed successfully!"
print_success "🌐 Your HR Portal has been updated!"

echo
echo "📊 Post-deployment checklist:"
echo "1. Test the application in your browser"
echo "2. Check logs: journalctl -u $SERVICE_NAME -f"
echo "3. Monitor for any errors"
echo "4. Verify all functionality works as expected"

# Display service status
echo
print_status "Current service status:"
systemctl status $SERVICE_NAME --no-pager -l