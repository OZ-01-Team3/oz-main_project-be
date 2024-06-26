from ast import literal_eval
from datetime import timedelta

import sentry_sdk

from tools.secrets import get_secret

from .base import *

ENV: dict[str, str] = literal_eval(get_secret())

SECRET_KEY = ENV["DJANGO_SECRET_KEY"]
DEBUG = True
ALLOWED_HOSTS = ENV["ALLOWED_HOSTS"].split(",")

DATABASES = {
    "default": {
        "ENGINE": ENV["DATABASE_ENGINE"],
        "NAME": ENV["DATABASE_NAME"],
        "USER": ENV["DATABASE_USER"],
        "PASSWORD": ENV["DATABASE_PASSWORD"],
        "HOST": ENV["DATABASE_HOST"],
        "PORT": ENV["DATABASE_PORT"],
    }
}

# cors 관련 설정
CORS_ALLOWED_ORIGINS = ENV["ORIGINS"].split(",")
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = ENV["ORIGINS"].split(",")
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

# csrf 관련 설정
# CSRF_TRUSTED_ORIGINS = ["http://*", "https://*"]
CSRF_TRUSTED_ORIGINS = ENV["ORIGINS"].split(",")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_DOMAIN = ENV["DOMAIN"]


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(ENV["REDIS_HOST"], ENV["REDIS_PORT"])],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{ENV['REDIS_HOST']}:{ENV['REDIS_PORT']}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": ENV["CACHES_PASSWORD"],
        },
    }
}

# djangorestframework-simplejwt 관련 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),  # default: minutes=5
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # default: days=1
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,  # default: False
    "ALGORITHM": ENV["JWT_ALGORITHM"],
    "SIGNING_KEY": ENV["DJANGO_SECRET_KEY"],
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
            # "session_profile": ENV("AWS_S3_SESSION_PROFILE"),
            "access_key": ENV["AWS_ACCESS_KEY_ID"],
            "secret_key": ENV["AWS_SECRET_ACCESS_KEY"],
            "bucket_name": ENV["AWS_STORAGE_BUCKET_NAME"],
            # "default_acl": ENV["AWS_DEFAULT_ACL"],
            "region_name": ENV["AWS_S3_REGION_NAME"],
            "use_ssl": ENV["AWS_S3_USE_SSL"],
            "custom_domain": ENV["AWS_STORAGE_BUCKET_NAME"] + ".s3.amazonaws.com",
            # "cloudfront_key": ENV["AWS_CLOUDFRONT_KEY"],
            # "cloudfront_key_id": ENV["AWS_CLOUDFRONT_KEY_ID"]
        },
    },
    "staticfiles": {
        # "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            # "session_profile": ENV("AWS_S3_SESSION_PROFILE"),
            "access_key": ENV["AWS_ACCESS_KEY_ID"],
            "secret_key": ENV["AWS_SECRET_ACCESS_KEY"],
            "bucket_name": ENV["AWS_STORAGE_BUCKET_NAME"],
            # "default_acl": ENV["AWS_DEFAULT_ACL"],
            "region_name": ENV["AWS_S3_REGION_NAME"],
            "use_ssl": ENV["AWS_S3_USE_SSL"],
            "custom_domain": ENV["AWS_STORAGE_BUCKET_NAME"] + ".s3.amazonaws.com",
            # "cloudfront_key": ENV["AWS_CLOUDFRONT_KEY"],
            # "cloudfront_key_id": ENV["AWS_CLOUDFRONT_KEY_ID"]
        },
    },
}

# django 이메일 인증 설정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = ENV["EMAIL_HOST"]  # 메일 호스트 서버
EMAIL_PORT = ENV["EMAIL_PORT"]
EMAIL_HOST_USER = ENV["EMAIL_HOST_USER"]  # 발신 이메일
EMAIL_HOST_PASSWORD = ENV["EMAIL_HOST_PASSWORD"]
EMAIL_USE_TLS = True  # TLS 보안
EMAIL_USE_SSL = False  # TODO
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# EMAIL_CONFIRMATION_AUTHENTICATED_REDIREDT_URL = "/"

sentry_sdk.init(
    dsn=ENV["SENTRY_DSN"],
    traces_sample_rate=float(ENV["SENTRY_TRACES_SAMPLE_RATE"]),
    profiles_sample_rate=float(ENV["SENTRY_PROFILES_SAMPLE_RATE"]),
)

# 커스텀 설정  # TODO
FRONT_CONFIRM_URL = ENV["FRONT_CONFIRM_URL"]
CONFIRM_CODE_LENGTH = ENV["CONFIRM_CODE_LENGTH"]
EMAIL_CODE_TIMEOUT = ENV["EMAIL_CODE_TIMEOUT"]
DJANGO_SUPERUSER_EMAIL = ENV["DJANGO_SUPERUSER_EMAIL"]
DJANGO_SUPERUSER_PASSWORD = ENV["DJANGO_SUPERUSER_PASSWORD"]

KAKAO_REDIRECT_URI = ENV["KAKAO_REDIRECT_URI"]
KAKAO_CLIENT_ID = ENV["KAKAO_CLIENT_ID"]
KAKAO_CLIENT_SECRET = ENV["KAKAO_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = ENV["GOOGLE_REDIRECT_URI"]
GOOGLE_CLIENT_ID = ENV["GOOGLE_CLIENT_ID"]
GOOGLE_SECRET = ENV["GOOGLE_SECRET"]
NAVER_REDIRECT_URI = ENV["NAVER_REDIRECT_URI"]
NAVER_CLIENT_ID = ENV["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = ENV["NAVER_CLIENT_SECRET"]
