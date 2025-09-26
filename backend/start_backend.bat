@echo off
cd /d C:\sales-portal\backend
call venv\Scripts\activate
set DJANGO_SETTINGS_MODULE=settings.production
set SECRET_KEY=your-secret-key-here
set ALLOWED_HOSTS=192.168.99.37,localhost
set DB_NAME=192.168.99.37:1521/XEPDB1
set DB_USER=salesportal
set DB_PASSWORD=salesportal123

echo Starting Django Backend...
python manage.py runserver 0.0.0.0:8000
