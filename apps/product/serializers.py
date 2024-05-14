# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField

from apps.product.models import Product, RentalHistory


class RentalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalHistory
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer[Product]):
    lender = ReadOnlyField(source="lender.nickname")
    rental_history = RentalHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "uuid",
            "name",
            "lender",
            "condition",
            "product_category",
            "purchasing_price",
            "rental_fee",
            "size",
            "views",
            "status",
            "created_at",
            "updated_at",
            "rental_history",
        )
        read_only_fields = ("created_at", "updated_at", "views", "lender", "status")
