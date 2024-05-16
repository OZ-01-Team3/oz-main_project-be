# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField

from apps.product.models import Product, RentalHistory
from apps.user.serializers import UserInfoSerializer


class RentalHistorySerializer(serializers.ModelSerializer[RentalHistory]):
    class Meta:
        model = RentalHistory
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer[Product]):
    # lender = ReadOnlyField(source="lender.nickname")
    lender = UserInfoSerializer(read_only=True)
    # rental_history = RentalHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "url",
            "uuid",
            "name",
            "lender",
            "brand",
            "condition",
            "description",
            "purchase_date",
            "purchase_price",
            "rental_fee",
            "size",
            "views",
            "product_category",
            "status",
            "amount",
            "region",
            "created_at",
            "updated_at",
            # "rental_history",
        )
        read_only_fields = ("created_at", "updated_at", "views", "lender", "status")
