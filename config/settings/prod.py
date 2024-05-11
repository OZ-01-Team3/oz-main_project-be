from ast import literal_eval

from tools.secrets import get_secret

from .base import *

DEBUG = True
ENV: dict[str, str] = literal_eval(get_secret())

SECRET_KEY = ENV["DJANGO_SECRET_KEY"]
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

CSRF_TRUSTED_ORIGINS = ENV["CSRF_TRUSTED_ORIGINS"].split(",")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(ENV["REDIS_HOST"], ENV["REDIS_PORT"])],
        },
    },
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
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
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
# URL_FRONT = ENV["URL_FRONT"]  # TODO 이건 어디서 나온 설정인지?
# EMAIL_CONFIRMATION_AUTHENTICATED_REDIREDT_URL = "/"

# 커스텀 설정  # TODO
FRONT_CONFIRM_URL = ENV["FRONT_CONFIRM_URL"]
GOOGLE_OAUTH2_URL = ENV["GOOGLE_OAUTH2_URL"]
