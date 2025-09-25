#!/bin/bash
# Production deployment script

echo "🚀 Starting production deployment..."

# Create logs directory
mkdir -p logs

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create cache table (if using database cache)
echo "🗂️ Creating cache table..."
python manage.py createcachetable

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (interactive)
echo "👤 Create superuser (if needed)..."
python manage.py createsuperuser

# Run Django deployment check
echo "🔍 Running deployment checklist..."
python manage.py check --deploy

echo "✅ Deployment complete!"
echo "🌐 Your application is ready for production!"