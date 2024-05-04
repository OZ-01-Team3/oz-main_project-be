from .base import *

# env = environ.Env(DEBUG=(bool, False))
# environ.Env.read_env(env_file=os.path.join(BASE_DIR / "env-be", ".env"))

DEBUG = True
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = ["127.0.0.1"]
