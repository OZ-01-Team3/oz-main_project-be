# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
from rest_framework.fields import ReadOnlyField

from apps.product.models import Product
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    user = ReadOnlyField(source="user.nickname")

    class Meta:
        model = Product
        fields = ("uuid", "name", "user", "condition", "product_category", "purchasing_price", "rental_fee", "size", "views", "status", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at", "views", "user")
