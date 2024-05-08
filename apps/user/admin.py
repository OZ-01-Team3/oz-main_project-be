import django_stubs_ext
from django.contrib import admin

from .models import Account

django_stubs_ext.monkeypatch()


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin[Account]):
    list_display = (
        "id",
        "email",
        "nickname",
        "age",
        "gender",
        "height",
        "region",
        "phone",
        "grade",
        "profile_img",
        "is_staff",
        "is_active",
        "is_superuser",
        "last_login",
        "updated_at",
        "created_at",
    )
    list_filter = (
        "age",
        "gender",
        "is_active",
    )
    search_fields = ("email", "nickname")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
