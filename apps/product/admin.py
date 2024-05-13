import django_stubs_ext
from django.contrib import admin

from .models import Product  # ProductImage, ProductCategory, StyleCategory

django_stubs_ext.monkeypatch()

# @admin.register(ProductCategory)
# class ProductCategoryAdmin(admin.ModelAdmin):
#     list_display = ['name']
#
# @admin.register(StyleCategory)
# class StyleCategoryAdmin(admin.ModelAdmin):
#     list_display = ['name']
#
# @admin.register(ProductImage)
# class ProductImageAdmin(admin.ModelAdmin):
#     list_display = ["id", "product", "image"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = [
        "name",
        "user",
        "condition",
        "purchasing_price",
        "rental_fee",
        "size",
        "views",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        # "product_category",
        # "style_category",
        "status",
        "created_at",
        "updated_at",
    ]
    search_fields = ["name", "user__username"]
