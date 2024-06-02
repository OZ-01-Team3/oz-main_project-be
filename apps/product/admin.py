import django_stubs_ext
from django.contrib import admin

from .models import (
    Product,
    RentalHistory,
)

django_stubs_ext.monkeypatch()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = [
        "uuid",
        "name",
        "lender",
        "condition",
        "purchase_price",
        "rental_fee",
        "size",
        "views",
        "status",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "product_category",
        "styles",
        "status",
        "created_at",
        "updated_at",
    ]
    search_fields = ["name", "lender__username"]

    # def rental_history(self, obj):
    #     return obj.rentalhistory_set()  # 관련 대여 기록 반환

    # rental_history.short_description = "Rental history"


@admin.register(RentalHistory)
class RentalHistoryAdmin(admin.ModelAdmin[RentalHistory]):
    list_display = [
        "id",
        "product",
        "status",
        # "product_lender",
        "rental_date",
        "return_date",
    ]
    list_filter = [
        "rental_date",
        "return_date",
    ]
    search_fields = ["product__name", "renter__username"]


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
