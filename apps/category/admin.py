import django_stubs_ext
from django.contrib import admin

from .models import Category, Style

django_stubs_ext.monkeypatch()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin[Category]):
    list_display = ("id", "name", "updated_at", "created_at")
    search_fields = ("name",)


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin[Style]):
    list_display = ("id", "name", "updated_at", "created_at")
    search_fields = ("name",)
