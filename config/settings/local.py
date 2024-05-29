import os
from datetime import timedelta

import environ
import sentry_sdk

from .base import *

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(env_file=os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = (
    ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE + ["whitenoise.middleware.WhiteNoiseMiddleware"]
)

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
            "hosts": [(env("REDIS_HOST"), env("REDIS_PORT"))],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{env('REDIS_HOST')}:{env('REDIS_PORT')}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": env("CACHES_PASSWORD"),
        },
    }
}

# cors 관련 설정
CORS_ALLOWED_ORIGINS = env("ORIGINS").split(",")
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = env("ORIGINS").split(",")

# csrf 관련 설정
# CSRF_TRUSTED_ORIGINS = ["http://*", "https://*"]
CSRF_TRUSTED_ORIGINS = env("ORIGINS").split(",")
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
# SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# djangorestframework-simplejwt 관련 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),  # default: minutes=5
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # default: days=1
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,  # default: False
    "ALGORITHM": env("JWT_ALGORITHM"),
    "SIGNING_KEY": env("DJANGO_SECRET_KEY"),
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

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
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
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


# django logging 설정
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
            "level": "INFO",
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

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE"),
    profiles_sample_rate=env.float("SENTRY_PROFILES_SAMPLE_RATE"),
)

DEBUG_TOOLBAR_CONFIG = {
    'IS_RUNNING_TESTS': False,
}

# 커스텀 설정  # TODO
FRONT_CONFIRM_URL = env("FRONT_CONFIRM_URL")
CONFIRM_CODE_LENGTH = env("CONFIRM_CODE_LENGTH")
EMAIL_CODE_TIMEOUT = env("EMAIL_CODE_TIMEOUT")
DJANGO_SUPERUSER_EMAIL = env("DJANGO_SUPERUSER_EMAIL")
DJANGO_SUPERUSER_PASSWORD = env("DJANGO_SUPERUSER_PASSWORD")
KAKAO_REDIRECT_URI = env("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_ID = env("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = env("KAKAO_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI")
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID")
GOOGLE_SECRET = env("GOOGLE_SECRET")
NAVER_REDIRECT_URI = env("NAVER_REDIRECT_URI")
NAVER_CLIENT_ID = env("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = env("NAVER_CLIENT_SECRET")
