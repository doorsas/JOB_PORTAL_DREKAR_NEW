# 🚀 Production Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. **Environment Setup**
- [ ] Copy `.env.example` to `.env` and fill in production values
- [ ] Generate a strong SECRET_KEY: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up PostgreSQL database (recommended over SQLite for production)

### 2. **Database Configuration**
- [ ] Install PostgreSQL and create database
- [ ] Update database settings in `.env` file
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Create cache table: `python manage.py createcachetable` (if using database cache)

### 3. **Static Files & Media**
- [ ] Run `python manage.py collectstatic --noinput`
- [ ] Configure web server (Nginx/Apache) to serve static files
- [ ] Set up media file handling (local storage or S3)
- [ ] Verify static files are served correctly

### 4. **Security Settings**
- [ ] SSL certificate installed and configured
- [ ] HTTPS redirect enabled
- [ ] Security headers configured
- [ ] Firewall configured (only allow necessary ports)
- [ ] Database connection secured

### 5. **Email Configuration**
- [ ] SMTP server configured
- [ ] Email credentials set in environment variables
- [ ] Test email sending functionality
- [ ] Configure error reporting emails

### 6. **Performance & Caching**
- [ ] Redis installed and configured (optional but recommended)
- [ ] Database query optimization reviewed
- [ ] Static file compression enabled (WhiteNoise)

### 7. **Monitoring & Logging**
- [ ] Log files directory created: `mkdir logs`
- [ ] Error tracking configured (Sentry optional)
- [ ] Monitor disk space, memory usage
- [ ] Set up backup procedures

## 🔧 Server Deployment Commands

### Using Gunicorn (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run deployment script
chmod +x deploy.sh
./deploy.sh

# Start with Gunicorn
gunicorn --config gunicorn.conf.py my_hr_portal.wsgi:application
```

### Using Docker (Alternative)
```bash
# Build Docker image
docker build -t hr-portal .

# Run container
docker run -p 8000:8000 --env-file .env hr-portal
```

## 🌍 Web Server Configuration (Nginx Example)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/your/media/;
    }
}
```

## 🔍 Testing & Validation

### Run Django's Deployment Check
```bash
python manage.py check --deploy
```

### Test Key Functionality
- [ ] User registration and login
- [ ] File uploads work
- [ ] Email sending works
- [ ] Database operations work
- [ ] Static files load correctly
- [ ] HTTPS redirects work
- [ ] Admin panel accessible

## 📊 Performance Monitoring

### Database Performance
- [ ] Monitor database connection pool
- [ ] Check for slow queries
- [ ] Set up database backups

### Application Performance
- [ ] Monitor memory usage
- [ ] Check response times
- [ ] Monitor error rates

## 🆘 Troubleshooting

### Common Issues
1. **Static files not loading**: Check `STATIC_ROOT` and web server configuration
2. **Database connection errors**: Verify database credentials and network access
3. **Email not sending**: Check SMTP settings and firewall rules
4. **SSL certificate issues**: Verify certificate installation and configuration

### Useful Commands
```bash
# Check Django deployment
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# Clear cache
python manage.py clearcache

# View logs
tail -f logs/django.log
tail -f logs/gunicorn_error.log
```

## 📝 Environment Variables Summary

Create `.env` file with these variables:
```
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True

ADMIN_EMAIL=admin@yourdomain.com
```

## 🎯 Go-Live Steps

1. **Final Testing**: Test all functionality on staging environment
2. **Backup**: Create backup of existing system (if applicable)
3. **Deploy**: Run deployment script
4. **Verify**: Check all services are running
5. **Monitor**: Watch logs for any issues
6. **Announce**: Notify users of new system

---

**Remember**: Always test your deployment on a staging environment first!