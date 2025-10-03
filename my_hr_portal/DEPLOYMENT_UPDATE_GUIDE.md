# HR Portal Deployment Update Guide

This guide explains how to update your deployed HR Portal application on Ubuntu.

## 🏗️ Your Current Setup

- **Server**: Ubuntu at `3.124.14.179`
- **Deploy Path**: `/var/www/hr-portal`
- **Service**: `hr-portal.service` (systemd)
- **Web Server**: Nginx
- **App Server**: Gunicorn
- **User**: `www-data`

## 📋 Available Update Methods

### Method 1: Automated Update Script (Recommended)

Use the automated update script that includes backup and rollback functionality:

```bash
# Copy the update script to your server
scp update-deploy.sh root@3.124.14.179:/tmp/

# SSH into your server
ssh root@3.124.14.179

# Run the update script
sudo bash /tmp/update-deploy.sh
```

**What this script does:**
- Creates automatic backup
- Updates code from Git repository
- Updates Python dependencies
- Runs database migrations
- Collects static files
- Restarts services
- Performs health checks
- Automatic rollback on failure

### Method 2: Git-Based Deployment

Use the Git deployment helper script:

```bash
# From your local development machine
./git-deploy.sh
```

This script will:
- Commit your local changes
- Push to remote Git repository
- Deploy to your Ubuntu server (via SSH)

### Method 3: Manual Update

If you prefer manual control:

```bash
# 1. SSH into your server
ssh root@3.124.14.179

# 2. Navigate to application directory
cd /var/www/hr-portal

# 3. Stop the service
sudo systemctl stop hr-portal

# 4. Backup current version
sudo tar -czf /var/backups/hr-portal/backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /var/www hr-portal

# 5. Update code (if using Git)
sudo -u www-data git pull origin master

# 6. Update dependencies
sudo -u www-data /var/www/hr-portal/venv/bin/pip install -r requirements.txt --upgrade

# 7. Run migrations
sudo -u www-data /var/www/hr-portal/venv/bin/python manage.py migrate

# 8. Collect static files
sudo -u www-data /var/www/hr-portal/venv/bin/python manage.py collectstatic --noinput

# 9. Restart services
sudo systemctl start hr-portal
sudo systemctl reload nginx
```

## 🔄 Rollback Process

If something goes wrong, use the rollback script:

```bash
# SSH into your server
ssh root@3.124.14.179

# Run rollback script
sudo bash /var/www/hr-portal/rollback.sh
```

The rollback script will:
- Show available backups
- Let you select which backup to restore
- Automatically restore the selected version
- Restart services

## 📁 File Structure

Your deployment scripts are located in your project:

```
my_hr_portal/
├── update-deploy.sh      # Main update script
├── git-deploy.sh         # Git-based deployment helper
├── rollback.sh          # Rollback to previous version
├── ubuntu-deploy.sh     # Initial server setup
├── gunicorn.conf.py     # Gunicorn configuration
├── nginx-hr-portal.conf # Nginx configuration
└── hr-portal.service    # Systemd service file
```

## 🚀 Quick Update Workflow

For regular updates, follow this workflow:

1. **Make your changes locally**
2. **Test changes** in development environment
3. **Commit changes** to Git
4. **Deploy to server** using one of the methods above
5. **Test deployed application**
6. **Monitor logs** for any issues

## 📊 Post-Deployment Checklist

After each deployment:

- [ ] Application loads in browser
- [ ] Login functionality works
- [ ] Database operations work
- [ ] Static files load correctly
- [ ] Check service logs: `journalctl -u hr-portal -f`
- [ ] Monitor error logs: `tail -f /var/www/hr-portal/logs/gunicorn_error.log`

## 🔧 Troubleshooting

### Service won't start
```bash
# Check service status
sudo systemctl status hr-portal

# Check logs
sudo journalctl -u hr-portal -f

# Check Gunicorn logs
sudo tail -f /var/www/hr-portal/logs/gunicorn_error.log
```

### Database issues
```bash
# Check database migrations
sudo -u www-data /var/www/hr-portal/venv/bin/python manage.py showmigrations

# Apply specific migration
sudo -u www-data /var/www/hr-portal/venv/bin/python manage.py migrate app_name migration_name
```

### Static files not loading
```bash
# Recollect static files
sudo -u www-data /var/www/hr-portal/venv/bin/python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

### Permission issues
```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/hr-portal
sudo chmod -R 755 /var/www/hr-portal
```

## 🛡️ Security Notes

- Always backup before updates
- Test updates in staging environment first
- Keep backups for at least 30 days
- Monitor logs after deployment
- Use SSH keys for authentication
- Keep system packages updated

## 📞 Emergency Contacts

If you encounter issues:
1. Check the logs first
2. Try the rollback script
3. Contact your system administrator
4. Document the issue for future reference

---

**Remember**: Always backup before making changes, and test thoroughly after deployment!