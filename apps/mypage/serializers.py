from rest_framework import serializers

from apps.category.models import Style
from apps.category.serializers import StyleSerializer
from apps.mypage.models import InterestedStyle
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


# class InterestedStyleSerializer(serializers.ModelSerializer):
#     styles = StyleSerializer(many=True)
#
#     class Meta:
#         model = InterestedStyle
#         fields = ("id", "styles")
#
#     def create(self, validated_data):
#         validated_data.pop("styles")
#         return InterestedStyle.objects.create(**validated_data)
#
#     def update(self, instance, validated_data):
#         instance.styles.clear()
#         styles_data = validated_data.pop("styles")
#         for item in styles_data:
#             style, created = Style.objects.get_or_create(**item)
#             instance.styles.add(style)
#         return instance
