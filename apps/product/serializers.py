# from rest_framework import serializers
# from apps.product.models import Product, ProductImage, ProductCategory, StyleCategory
# from apps.user.models import Account
import logging
from typing import Any

from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.category.models import Style
from apps.like.models import Like
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
    is_liked = serializers.SerializerMethodField()

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
            "styles",
            "status",
            "amount",
            "region",
            "created_at",
            "updated_at",
            "images",
            "likes",
            "is_liked",
            # "rental_history",
        )
        read_only_fields = ("created_at", "updated_at", "views", "lender", "status", "likes", "is_liked")

    def get_is_liked(self, obj) -> bool:
        user = self.context["request"].user
        if user.is_authenticated:
            return Like.objects.filter(user=user, product=obj).exists()
        return False

    def set_styles(self, styles_data):
        styles = []
        for style in styles_data:
            style_name = style.name
            style_item, _ = Style.objects.get_or_create(name=style_name)
            styles.append(style)
        return styles

    @transaction.atomic
    def create(self, validated_data: Any) -> Product:
        image_set = self.context["request"].FILES.getlist("image")
        styles_data = validated_data.pop("styles", [])
        product = Product.objects.create(**validated_data)

        styles = self.set_styles(styles_data)
        product.styles.set(styles)

        if image_set:
            product_images = [ProductImage(product=product, image=image) for image in image_set]
            ProductImage.objects.bulk_create(product_images)
        return product

    @transaction.atomic
    def update(self, instance: Product, validated_data: Any) -> Product:
        request = self.context["request"]
        received_new_images = request.FILES.getlist("image")
        received_existing_images = request.POST.getlist("image")
        styles_data = validated_data.pop("styles", [])

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

        # styles 태그 등록
        styles = self.set_styles(styles_data)
        instance.styles.set(styles)
        return instance
