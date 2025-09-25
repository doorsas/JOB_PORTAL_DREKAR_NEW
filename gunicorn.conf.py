# Gunicorn configuration file for Ubuntu production

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes - adjust based on server resources
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
base_dir = "/var/www/hr-portal"
accesslog = f"{base_dir}/logs/gunicorn_access.log"
errorlog = f"{base_dir}/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "hr_portal"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/hr-portal/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=my_hr_portal.settings.production',
]

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if terminating SSL at Gunicorn level - not needed with Nginx)
# keyfile = "/etc/ssl/private/your-domain.key"
# certfile = "/etc/ssl/certs/your-domain.crt"

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use RAM disk for better performance
forwarded_allow_ips = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"