from rest_framework import serializers

from apps.like.models import Like
from apps.product.serializers import ProductSerializer


class LikeSerializer(serializers.ModelSerializer[Like]):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "product")
