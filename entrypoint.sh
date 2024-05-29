#!/bin/sh

ln -sf prod.py config/settings/settings.py
#ln -sf local.py config/settings/settings.py
#sudo apt-get update
#sudo apt-get install vim -y
export DJANGO_SETTINGS_MODULE=config.settings.settings

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py shell < tools/create_superuser.py
#python manage.py runserver 0.0.0.0:80

#gunicorn --bind 0.0.0.0:8001 config.wsgi:application
#uvicorn config.asgi:application --workers 4
#gunicorn config.asgi:application  -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

gunicorn config.asgi:application -c tools/gunicorn_prod.conf.py
