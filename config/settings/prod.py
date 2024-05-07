from .base import *

DEBUG = True
ALLOWED_HOSTS = env("ALLOWED_HOSTS_PROD").split(",")

DATABASES = {
    "default": {
        "ENGINE": env("DATABASE_ENGINE"),
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST_PROD"),
        "PORT": env("DATABASE_PORT"),
    }
}

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS").split(",")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
