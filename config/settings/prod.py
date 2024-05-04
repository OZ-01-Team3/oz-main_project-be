from .base import *

DEBUG = False
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
