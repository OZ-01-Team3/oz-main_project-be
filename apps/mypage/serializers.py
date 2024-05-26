from rest_framework import serializers

from apps.product.models import Product


class MyProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
