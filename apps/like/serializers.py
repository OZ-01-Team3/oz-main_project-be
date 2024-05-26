from rest_framework import serializers

from apps.like.models import Like
from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class LikeSerializer(serializers.ModelSerializer[Like]):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "product_id", "product")
