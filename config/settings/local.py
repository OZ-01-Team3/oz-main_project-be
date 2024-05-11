# import os
import environ

from .base import *

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(env_file=os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = ["127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": env("DATABASE_ENGINE"),
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env("REDIS_HOST"), 6379)],
        },
    },
}

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/0",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }

CSRF_TRUSTED_ORIGINS = ["http://*", "https://*"]

# S3 관련 설정
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            # "session_profile": env("AWS_S3_SESSION_PROFILE"),
            "access_key": env("AWS_ACCESS_KEY_ID"),
            "secret_key": env("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            # "default_acl": env("AWS_DEFAULT_ACL"),
            "region_name": env("AWS_S3_REGION_NAME"),
            "use_ssl": env("AWS_S3_USE_SSL"),
            "custom_domain": env("AWS_STORAGE_BUCKET_NAME") + ".s3.amazonaws.com",
            # "cloudfront_key": env("AWS_CLOUDFRONT_KEY"),
            # "cloudfront_key_id": env("AWS_CLOUDFRONT_KEY_ID")
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# django 이메일 인증 설정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")  # 메일 호스트 서버
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")  # 발신 이메일
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True  # TLS 보안
EMAIL_USE_SSL = False  # TODO
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# URL_FRONT = env("URL_FRONT")  # TODO 이건 어디서 나온 설정인지?
# EMAIL_CONFIRMATION_AUTHENTICATED_REDIREDT_URL = "/"


log_file_path = os.path.join(BASE_DIR, "logs", "django.log")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        # "file": {
        #     "level": "DEBUG",
        #     "class": "logging.FileHandler",
        #     "filename": log_file_path,
        # },
        "file": {
            "level": "INFO",
            # 'filters': ['require_debug_false'],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file_path,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "standard",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
