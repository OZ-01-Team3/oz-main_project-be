# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
from typing import Any

from rest_framework import serializers
from rest_framework.fields import ReadOnlyField
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.product.models import Product, ProductImage, RentalHistory
from apps.user.serializers import UserInfoSerializer


class RentalHistorySerializer(serializers.ModelSerializer[RentalHistory]):
    class Meta:
        model = RentalHistory
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer[ProductImage]):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ProductImage
        fields = ("id", "image")


class ProductSerializer(serializers.ModelSerializer[Product]):
    # lender = ReadOnlyField(source="lender.nickname")
    lender = UserInfoSerializer(read_only=True)
    # rental_history = RentalHistorySerializer(many=True, read_only=True)
    # images = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

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
            "images",
            # "rental_history",
        )
        read_only_fields = ("created_at", "updated_at", "views", "lender", "status")

    # def get_images(self, obj: Product) -> ReturnDict | ReturnDict:
    #     images = obj.images.all()
    #     return ProductImageSerializer(instance=images, many=True).data
    #     # return ProductImageSerializer(images, many=True, context=self.context).data

    def create(self, validated_data: Any) -> Product:
        image_set = self.context["request"].FILES
        product = Product.objects.create(**validated_data)
        for image in image_set.getlist("image"):
            ProductImage.objects.create(product=product, image=image)
        return product

    def update(self, instance: Product, validated_data: Any) -> Product:
        image_set = self.context["request"].FILES
        existing_images = set(instance.images.values_list("id", flat=True))
        new_images = set()
        if image_set:
            for image in image_set.getlist("image"):
                new_image = ProductImage.objects.create(product=instance, image=image)
                new_images.add(new_image.id)
        images_to_delete = existing_images - new_images
        ProductImage.objects.filter(id__in=images_to_delete).delete()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
