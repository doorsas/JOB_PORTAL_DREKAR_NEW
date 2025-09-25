# 🚀 Ubuntu Lightsail Deployment Guide

Complete guide to deploy your HR Portal on Ubuntu server with Nginx and SSL.

## 📋 **Pre-Deployment Checklist**

- [x] Ubuntu server on AWS Lightsail
- [x] Static IP configured (3.124.14.179)
- [x] Nginx installed
- [ ] Domain name pointed to your server (optional but recommended)
- [ ] SSH access to server

## 🔧 **Step 1: Server Preparation**

### **1.1 Connect to Your Server**
```bash
ssh ubuntu@3.124.14.179
```

### **1.2 Run Initial Setup Script**
```bash
# Upload and run the setup script
wget https://your-server/ubuntu-deploy.sh
chmod +x ubuntu-deploy.sh
sudo ./ubuntu-deploy.sh
```

Or manually install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev nginx supervisor git curl certbot python3-certbot-nginx
```

## 📦 **Step 2: Deploy Application Code**

### **2.1 Upload Your Code**
```bash
# Method 1: Using Git (recommended)
sudo mkdir -p /var/www/hr-portal
sudo chown www-data:www-data /var/www/hr-portal
cd /var/www/hr-portal
sudo -u www-data git clone https://github.com/yourusername/hr-portal.git .

# Method 2: Using SCP from your local machine
scp -r C:\Users\PC\NEW_JOB_PORTAL\my_hr_portal ubuntu@3.124.14.179:/tmp/
sudo mv /tmp/my_hr_portal /var/www/hr-portal
sudo chown -R www-data:www-data /var/www/hr-portal
```

### **2.2 Set Up Python Environment**
```bash
cd /var/www/hr-portal
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### **2.3 Configure Environment**
```bash
# Copy and edit environment file
sudo -u www-data cp .env.example .env
sudo -u www-data nano .env
```

Update `.env` with:
```env
DEBUG=False
SECRET_KEY=74%3h#+-@xo^#-f)58+$kii1r6h%g5c(bkambp)eg1b@!d_rjz
ALLOWED_HOSTS=3.124.14.179,your-domain.com,www.your-domain.com
DATABASE_URL=sqlite:///db.sqlite3
SECURE_SSL_REDIRECT=True
```

## 🗄️ **Step 3: Database Setup**

### **3.1 Run Migrations**
```bash
cd /var/www/hr-portal
sudo -u www-data venv/bin/python manage.py migrate
```

### **3.2 Create Superuser**
```bash
sudo -u www-data venv/bin/python manage.py createsuperuser
```

### **3.3 Collect Static Files**
```bash
sudo -u www-data venv/bin/python manage.py collectstatic --noinput
```

### **3.4 Create Cache Table (if using database cache)**
```bash
sudo -u www-data venv/bin/python manage.py createcachetable
```

## 🚀 **Step 4: Set Up Gunicorn Service**

### **4.1 Copy Systemd Service File**
```bash
sudo cp /var/www/hr-portal/hr-portal.service /etc/systemd/system/
```

### **4.2 Enable and Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable hr-portal
sudo systemctl start hr-portal
sudo systemctl status hr-portal
```

## 🌐 **Step 5: Configure Nginx**

### **5.1 Copy Nginx Configuration**
```bash
sudo cp /var/www/hr-portal/nginx-hr-portal.conf /etc/nginx/sites-available/hr-portal
sudo ln -s /etc/nginx/sites-available/hr-portal /etc/nginx/sites-enabled/
```

### **5.2 Remove Default Nginx Site**
```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

### **5.3 Test Nginx Configuration**
```bash
sudo nginx -t
```

### **5.4 Restart Nginx**
```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🔒 **Step 6: Set Up SSL Certificate (Let's Encrypt)**

### **6.1 Install SSL Certificate**
```bash
# For domain-based setup
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# For IP-based setup (not recommended for production)
sudo certbot --nginx
```

### **6.2 Test SSL Renewal**
```bash
sudo certbot renew --dry-run
```

### **6.3 Enable Auto-Renewal**
```bash
sudo crontab -e
# Add this line:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔥 **Step 7: Configure Firewall**

### **7.1 Set Up UFW**
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 📊 **Step 8: Set Up Logging & Monitoring**

### **8.1 Create Log Directories**
```bash
sudo mkdir -p /var/www/hr-portal/logs
sudo chown -R www-data:www-data /var/www/hr-portal/logs
```

### **8.2 Set Up Log Rotation**
```bash
sudo nano /etc/logrotate.d/hr-portal
```

Add:
```
/var/www/hr-portal/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload hr-portal
    endscript
}
```

## ✅ **Step 9: Final Testing**

### **9.1 Check All Services**
```bash
sudo systemctl status hr-portal
sudo systemctl status nginx
sudo systemctl status certbot.timer
```

### **9.2 Test Website**
- Visit: `https://3.124.14.179`
- Admin: `https://3.124.14.179/admin`
- Check SSL: Use SSL Labs test

### **9.3 Test Application Features**
- [ ] User registration/login
- [ ] File uploads
- [ ] Email functionality
- [ ] Static files loading
- [ ] Admin panel access

## 🔧 **Maintenance Commands**

### **Update Application**
```bash
cd /var/www/hr-portal
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo -u www-data venv/bin/python manage.py migrate
sudo -u www-data venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart hr-portal
```

### **View Logs**
```bash
# Application logs
sudo journalctl -u hr-portal -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Django logs
sudo tail -f /var/www/hr-portal/logs/django.log
```

### **Restart Services**
```bash
sudo systemctl restart hr-portal
sudo systemctl restart nginx
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Service won't start:**
   ```bash
   sudo journalctl -u hr-portal --no-pager
   ```

2. **Static files not loading:**
   ```bash
   sudo -u www-data python manage.py collectstatic --noinput
   sudo systemctl restart nginx
   ```

3. **SSL certificate issues:**
   ```bash
   sudo certbot certificates
   sudo certbot renew
   ```

4. **Permission issues:**
   ```bash
   sudo chown -R www-data:www-data /var/www/hr-portal
   ```

## 📈 **Performance Optimization**

### **For High Traffic:**
- Set up PostgreSQL database
- Configure Redis for caching
- Use CDN for static files
- Set up load balancer

### **Database Upgrade to PostgreSQL:**
```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb hrportal
sudo -u postgres createuser hruser
sudo -u postgres psql -c "ALTER USER hruser WITH PASSWORD 'securepassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hrportal TO hruser;"

# Update .env
DATABASE_URL=postgresql://hruser:securepassword@localhost:5432/hrportal
```

## 🎯 **Production URLs**

- **Website**: `https://3.124.14.179`
- **Admin Panel**: `https://3.124.14.179/admin`
- **API Endpoints**: `https://3.124.14.179/api/`

---

🎉 **Your HR Portal is now live on Ubuntu Lightsail!**

Remember to:
- [ ] Set up regular backups
- [ ] Monitor server performance
- [ ] Keep dependencies updated
- [ ] Monitor logs for errors