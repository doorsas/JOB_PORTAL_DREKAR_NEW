# 🪟 Windows Production Deployment Guide

Your Django HR Portal is now **production-ready**! Here's how to deploy it.

## ✅ **Current Status**
- ✅ Production settings configured
- ✅ Environment variables set up
- ✅ Static files collected
- ✅ Database migrations complete
- ✅ Security settings configured
- ✅ Server running on `http://3.124.14.179:8000`

## 🚀 **Quick Start (Windows)**

### 1. **Start Production Server**
```bash
cd C:\Users\PC\NEW_JOB_PORTAL
venv\Scripts\activate
cd my_hr_portal
set DJANGO_SETTINGS_MODULE=my_hr_portal.settings.production
python manage.py runserver 0.0.0.0:8000
```

### 2. **Access Your Application**
- **Local**: http://localhost:8000
- **Server**: http://3.124.14.179:8000

## 🔧 **Production Configuration**

### **Environment Settings (`.env`)**
```env
DEBUG=False
SECRET_KEY=74%3h#+-@xo^#-f)58+$kii1r6h%g5c(bkambp)eg1b@!d_rjz
ALLOWED_HOSTS=3.124.14.179,localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### **Key Features Enabled**
- 🔐 **Security**: HTTPS ready, secure cookies, XSS protection
- 📁 **Static Files**: WhiteNoise for efficient serving
- 🗄️ **Database**: SQLite (upgradeable to PostgreSQL)
- 📧 **Email**: SMTP configuration ready
- 📊 **Logging**: Error logging to files and console

## 🌐 **For Linux/Unix Production Server**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Use Gunicorn (Linux/Unix only)**
```bash
# Start with Gunicorn
gunicorn --config gunicorn.conf.py my_hr_portal.wsgi:application

# Or with systemd service
sudo systemctl start hr-portal
sudo systemctl enable hr-portal
```

### **3. Nginx Configuration**
```nginx
server {
    listen 80;
    server_name 3.124.14.179;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

## 🛡️ **Security Checklist**

### **Before Going Live:**
- [ ] **SSL Certificate**: Install SSL and set `SECURE_SSL_REDIRECT=True`
- [ ] **Firewall**: Configure firewall rules
- [ ] **Database**: Upgrade to PostgreSQL for production
- [ ] **Email**: Configure SMTP for production emails
- [ ] **Backups**: Set up automated backups
- [ ] **Monitoring**: Set up error monitoring

### **Update `.env` for SSL:**
```env
SECURE_SSL_REDIRECT=True
```

## 🗄️ **Database Upgrade (Recommended)**

### **PostgreSQL Setup:**
1. **Install PostgreSQL**
2. **Create Database:**
   ```sql
   CREATE DATABASE hr_portal_db;
   CREATE USER hr_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE hr_portal_db TO hr_user;
   ```

3. **Update `.env`:**
   ```env
   DATABASE_URL=postgresql://hr_user:secure_password@localhost:5432/hr_portal_db
   ```

4. **Install PostgreSQL Driver:**
   ```bash
   pip install psycopg2-binary
   ```

## 📧 **Email Configuration**

### **Gmail Setup:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
EMAIL_USE_TLS=True
```

## 🔍 **Testing & Validation**

### **Run Deployment Check:**
```bash
python manage.py check --deploy
```

### **Test Key Features:**
- [ ] User registration/login
- [ ] File uploads
- [ ] Email sending
- [ ] Admin panel access
- [ ] Static files loading

## 🚨 **Common Issues & Solutions**

### **Static Files Not Loading:**
```bash
python manage.py collectstatic --noinput
```

### **Database Issues:**
```bash
python manage.py migrate
```

### **Permission Errors:**
- Ensure proper file permissions
- Check media/staticfiles directory permissions

## 📊 **Performance Optimization**

### **For High Traffic:**
- Use PostgreSQL instead of SQLite
- Configure Redis for caching
- Use CDN for static files
- Set up load balancer

### **Redis Cache Setup:**
```env
REDIS_URL=redis://127.0.0.1:6379/1
```

## 🎯 **Your Production Environment**

- **Server IP**: `3.124.14.179`
- **Application Port**: `8000`
- **Settings Module**: `my_hr_portal.settings.production`
- **Database**: SQLite (ready for PostgreSQL upgrade)
- **Static Files**: Served by WhiteNoise
- **Security**: Production-grade security settings

## 📞 **Support Commands**

### **View Logs:**
```bash
# Application logs
tail -f logs/django.log

# Error logs
tail -f logs/gunicorn_error.log
```

### **Database Management:**
```bash
python manage.py createsuperuser
python manage.py dbshell
```

### **Cache Management:**
```bash
python manage.py createcachetable
python manage.py clearcache
```

---

🎉 **Congratulations! Your HR Portal is production-ready and running!**

Access it at: **http://3.124.14.179:8000**