from django.core.cache import cache


def get_or_set_cache(key, queryset, timeout):
    return cache.get_or_set(key, queryset, timeout)


def get_cache(key):
    return cache.get(key)


def set_cache(key, value, timeout):
    cache.set(key, value, timeout)


def clear_cache(key):
    cache.delete(key)
