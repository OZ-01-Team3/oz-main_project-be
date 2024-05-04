import os
from django.contrib.auth import get_user_model

Account = get_user_model()

DJANGO_SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL')
DJANGO_SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if Account.objects.filter(email=DJANGO_SUPERUSER_EMAIL).exists():
    print("Superuser is already initialized!")
else:
    print("Initializing superuser...")
    try:
        superuser = Account.objects.create_superuser(
            email=DJANGO_SUPERUSER_EMAIL,
            password=DJANGO_SUPERUSER_PASSWORD)
        superuser.save()
        print("Superuser initialized!")
    except Exception as e:
        print(e)
