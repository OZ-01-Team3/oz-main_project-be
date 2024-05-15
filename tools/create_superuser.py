import os
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model

Account = get_user_model()

if os.readlink("config/settings/settings.py") == "prod.py":
    DJANGO_SUPERUSER_EMAIL = settings.DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_PASSWORD = settings.DJANGO_SUPERUSER_PASSWORD
else:
    DJANGO_SUPERUSER_EMAIL = str(os.environ.get("DJANGO_SUPERUSER_EMAIL"))
    DJANGO_SUPERUSER_PASSWORD = str(os.environ.get("DJANGO_SUPERUSER_PASSWORD"))


if DJANGO_SUPERUSER_EMAIL is None or DJANGO_SUPERUSER_PASSWORD is None:
    print("Please set DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD environment variables.")
else:
    if Account.objects.filter(email=DJANGO_SUPERUSER_EMAIL).exists():
        print("Superuser is already initialized!")
    else:
        print("Initializing superuser...")
        try:
            superuser: Any = Account.objects.create_superuser(
                email=DJANGO_SUPERUSER_EMAIL, password=DJANGO_SUPERUSER_PASSWORD
            )
            superuser.save()
            print("Superuser initialized!")
        except Exception as e:
            print(e)
