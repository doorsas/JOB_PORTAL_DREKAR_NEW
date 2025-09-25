# 🚀 Quick Ubuntu Deployment Commands

Copy and paste these commands on your Ubuntu Lightsail server:

## 📦 **1. Initial Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev nginx supervisor git curl certbot python3-certbot-nginx

# Create application directory
sudo mkdir -p /var/www/hr-portal
sudo chown www-data:www-data /var/www/hr-portal
```

## 📁 **2. Upload and Setup Application**
```bash
# Navigate to app directory
cd /var/www/hr-portal

# Create Python virtual environment
sudo -u www-data python3 -m venv venv

# Upload your project files here (using scp, git, or FTP)
# Then continue with:

# Install Python dependencies
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt

# Create logs directory
sudo mkdir -p logs
sudo chown -R www-data:www-data logs
```

## ⚙️ **3. Configure Environment**
```bash
# Copy environment file
sudo -u www-data cp .env.example .env

# Edit environment file (update with your settings)
sudo -u www-data nano .env
```

## 🗄️ **4. Database Setup**
```bash
cd /var/www/hr-portal

# Run migrations
sudo -u www-data venv/bin/python manage.py migrate

# Collect static files
sudo -u www-data venv/bin/python manage.py collectstatic --noinput

# Create superuser (interactive)
sudo -u www-data venv/bin/python manage.py createsuperuser
```

## 🚀 **5. Setup Gunicorn Service**
```bash
# Copy systemd service file
sudo cp hr-portal.service /etc/systemd/system/

# Create PID directory
sudo mkdir -p /var/run/hr-portal
sudo chown www-data:www-data /var/run/hr-portal

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hr-portal
sudo systemctl start hr-portal

# Check status
sudo systemctl status hr-portal
```

## 🌐 **6. Configure Nginx**
```bash
# Copy Nginx configuration
sudo cp nginx-hr-portal.conf /etc/nginx/sites-available/hr-portal

# Enable the site
sudo ln -s /etc/nginx/sites-available/hr-portal /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🔒 **7. Setup SSL (Let's Encrypt)**
```bash
# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# For IP-only setup (not recommended for production)
# sudo certbot --nginx

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🔥 **8. Configure Firewall**
```bash
# Setup firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## ✅ **9. Final Check**
```bash
# Check all services
sudo systemctl status hr-portal nginx

# View logs if needed
sudo journalctl -u hr-portal -f
```

## 🔧 **Useful Maintenance Commands**

### **Restart Application**
```bash
sudo systemctl restart hr-portal
```

### **Update Application**
```bash
cd /var/www/hr-portal
sudo -u www-data git pull  # if using git
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo -u www-data venv/bin/python manage.py migrate
sudo -u www-data venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart hr-portal
```

### **View Logs**
```bash
# Application logs
sudo journalctl -u hr-portal -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Django application logs
sudo tail -f /var/www/hr-portal/logs/django.log
```

### **Check SSL Certificate**
```bash
sudo certbot certificates
sudo certbot renew
```

---

🎯 **Your application will be available at:**
- **HTTP**: `http://3.124.14.179` (redirects to HTTPS)
- **HTTPS**: `https://3.124.14.179`
- **Admin**: `https://3.124.14.179/admin`