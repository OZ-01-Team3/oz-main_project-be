# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
import logging
from typing import Any

from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.product.models import Product, ProductImage, RentalHistory
from apps.user.serializers import UserInfoSerializer

logger = logging.getLogger(__name__)


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

    @transaction.atomic
    def create(self, validated_data: Any) -> Product:
        image_set = self.context["request"].FILES.getlist("image")
        product = Product.objects.create(**validated_data)
        if image_set:
            product_images = [ProductImage(product=product, image=image) for image in image_set]
            ProductImage.objects.bulk_create(product_images)
        return product

    @transaction.atomic
    def update(self, instance: Product, validated_data: Any) -> Product:
        request = self.context["request"]
        received_new_images = request.FILES.getlist("image")
        received_existing_images = request.POST.getlist("image")

        # 기존 이미지와 받은 이미지 id 비교해서 다시 안 온 이미지 삭제
        existing_images = {img.get_image_url(): img.id for img in instance.images.all()}
        valid_existing_image_id_set = {
            existing_images.get(link) for link in received_existing_images if link in existing_images
        }
        images_to_delete = set(existing_images.values()) - valid_existing_image_id_set
        ProductImage.objects.filter(id__in=images_to_delete).delete()

        # 새로운 이미지 파일 등록
        if received_new_images:
            product_images = [ProductImage(product=instance, image=image) for image in received_new_images]
            ProductImage.objects.bulk_create(product_images)

        # product 정보 수정
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
