from django.core.cache import cache


def clear_cache(key):
    cache.delete(key)
