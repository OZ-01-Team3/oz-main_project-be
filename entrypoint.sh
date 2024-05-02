#!/bin/sh

python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:80

#gunicorn --bind 0:80 config.wsgi:application
