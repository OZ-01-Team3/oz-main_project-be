from .base import *

# env = environ.Env(DEBUG=(bool, False))
# environ.Env.read_env(env_file=os.path.join(BASE_DIR / "env-be", ".env"))

DEBUG = True
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")
