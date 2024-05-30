from typing import Any

from django.core.cache import cache
from django.db.models import QuerySet


def get_or_set_cache(key: str, queryset: QuerySet[Any], timeout: int) -> QuerySet[Any] | None:
    return cache.get_or_set(key, queryset, timeout)


def get_cache(key: str) -> Any:
    return cache.get(key)


def set_cache(key: str, value: QuerySet[Any], timeout: int) -> None:
    cache.set(key, value, timeout)


def clear_cache(key: str) -> None:
    cache.delete(key)
