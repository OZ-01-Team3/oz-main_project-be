#!/bin/sh

ln -sf prod.py config/settings/settings.py
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py shell < tools/create_superuser.py
#python manage.py runserver 0.0.0.0:80

gunicorn --bind 0:8000 config.wsgi:application
