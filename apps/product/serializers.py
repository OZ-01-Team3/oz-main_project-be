import logging
from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.category.models import Category, Style
from apps.like.models import Like
from apps.product.models import Product, ProductImage, RentalHistory
from apps.user.serializers import UserInfoSerializer

logger = logging.getLogger(__name__)


class ProductImageSerializer(serializers.ModelSerializer[ProductImage]):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ProductImage
        fields = ("id", "image")


class ProductSerializer(serializers.ModelSerializer[Product]):
    lender = UserInfoSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    product_category = serializers.SlugRelatedField(slug_field="name", queryset=Category.objects.all())
    styles = serializers.SlugRelatedField(many=True, slug_field="name", queryset=Style.objects.all())

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
        )
        read_only_fields = ("created_at", "updated_at", "views", "lender", "status", "likes", "is_liked")

    def get_is_liked(self, obj: Product) -> bool:
        user = self.context["request"].user
        if user.is_authenticated:
            return Like.objects.filter(user=user, product=obj).exists()
        return False

    def set_styles(self, styles_data: list[Style]) -> list[Style]:
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


class ProductInfoSerializer(serializers.ModelSerializer[Product]):
    style = serializers.SerializerMethodField()  # type:ignore
    category = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "uuid",
            "name",
            "brand",
            "size",
            "purchase_price",
            "rental_fee",
            "category",
            "style",
            "images",
            "description",
        ]

    def get_style(self, obj: Product) -> list[str]:
        return [style.name for style in obj.styles.all()]

    def get_category(self, obj: Product) -> str:
        return obj.product_category.name


class RentalHistorySerializer(serializers.ModelSerializer[RentalHistory]):
    product_info = ProductInfoSerializer(read_only=True, source="product")
    lender_nickname = serializers.SerializerMethodField()
    borrower_nickname = serializers.SerializerMethodField()
    borrower_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RentalHistory
        exclude = ("borrower",)
        read_only_fields = ("created_at", "updated_at")

    def get_lender_nickname(self, obj: RentalHistory) -> str:
        return obj.product.lender.nickname

    def get_borrower_nickname(self, obj: RentalHistory) -> str:
        return obj.borrower.nickname

    def to_representation(self, instance: RentalHistory) -> dict[str, Any]:
        data = super().to_representation(instance)
        if instance.status == "REQUEST":
            data["status"] = "대여 요청"
        elif instance.status == "ACCEPT":
            data["status"] = "대여 요청 수락"
        elif instance.status == "RETURNED":
            data["status"] = "반납 완료"
        elif instance.status == "BORROWING":
            data["status"] = "대여 진행중"
        return data


class RentalHistoryStatusSerializer(serializers.ModelSerializer[RentalHistory]):
    class Meta:
        model = RentalHistory
        fields = ("id", "status", "rental_date", "return_date")
