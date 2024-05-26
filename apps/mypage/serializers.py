from rest_framework import serializers

from apps.product.models import Product
from apps.product.serializers import ProductImageSerializer


class MyProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "url",
            "uuid",
            "name",
            "brand",
            "condition",
            "description",
            "purchase_date",
            "purchase_price",
            "rental_fee",
            "size",
            "views",
            "product_category",
            "styles",
            "status",
            "amount",
            "region",
            "created_at",
            "updated_at",
            "images",
        )
