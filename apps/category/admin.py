import django_stubs_ext
from django.contrib import admin

from .models import Category

django_stubs_ext.monkeypatch()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin[Category]):
    list_display = ("id", "name", "updated_at", "created_at")
    search_fields = ("name",)
