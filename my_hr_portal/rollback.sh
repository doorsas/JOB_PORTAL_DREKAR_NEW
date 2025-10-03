#!/bin/bash
# HR Portal Rollback Script
# This script helps you rollback to a previous backup

set -e

# Configuration
APP_NAME="hr-portal"
APP_USER="www-data"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="hr-portal"
BACKUP_DIR="/var/backups/$APP_NAME"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "HR Portal Rollback Tool"
echo

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# List available backups
print_status "Available backups:"
backups=($(ls -t $BACKUP_DIR/backup_*.tar.gz 2>/dev/null))

if [ ${#backups[@]} -eq 0 ]; then
    print_error "No backups found in $BACKUP_DIR"
    exit 1
fi

# Display backups with selection
for i in "${!backups[@]}"; do
    backup_file=$(basename "${backups[$i]}")
    # Extract timestamp from filename
    timestamp=${backup_file#backup_}
    timestamp=${timestamp%.tar.gz}
    # Format timestamp for display
    formatted_date=$(date -d "${timestamp:0:8} ${timestamp:9:2}:${timestamp:11:2}:${timestamp:13:2}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$timestamp")
    echo "$((i+1))) $backup_file (Created: $formatted_date)"
done

echo
read -p "Select backup to restore (1-${#backups[@]}): " selection

# Validate selection
if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt ${#backups[@]} ]; then
    print_error "Invalid selection"
    exit 1
fi

selected_backup="${backups[$((selection-1))]}"
backup_name=$(basename "$selected_backup")

print_warning "⚠️  This will rollback your application to: $backup_name"
print_warning "⚠️  Current application will be REPLACED!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_status "Rollback cancelled"
    exit 0
fi

print_status "Starting rollback process..."

# Create a backup of current state before rollback
current_backup="$BACKUP_DIR/pre_rollback_$(date +%Y%m%d_%H%M%S).tar.gz"
print_status "Creating backup of current state..."
tar -czf "$current_backup" -C "/var/www" "$APP_NAME"
print_success "Current state backed up to: $current_backup"

# Stop the service
print_status "Stopping $SERVICE_NAME service..."
systemctl stop $SERVICE_NAME

# Remove current application
print_status "Removing current application..."
rm -rf $APP_DIR

# Extract selected backup
print_status "Restoring from backup: $backup_name"
cd /var/www
tar -xzf "$selected_backup"

# Set proper permissions
print_status "Setting proper permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR

# Start services
print_status "Starting services..."
systemctl start $SERVICE_NAME
systemctl reload nginx

# Wait for services to start
sleep 3

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "$SERVICE_NAME is running"
else
    print_error "$SERVICE_NAME failed to start after rollback"
    print_error "Check logs: journalctl -u $SERVICE_NAME -f"
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

print_success "✅ Rollback completed successfully!"
print_success "🌐 Your HR Portal has been restored to: $backup_name"

echo
echo "📊 Post-rollback checklist:"
echo "1. Test the application in your browser"
echo "2. Check logs: journalctl -u $SERVICE_NAME -f"
echo "3. Verify all functionality works as expected"
echo "4. Current state was backed up to: $current_backup"

# Display service status
echo
print_status "Current service status:"
systemctl status $SERVICE_NAME --no-pager -l