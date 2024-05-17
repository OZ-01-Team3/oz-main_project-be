from rest_framework import serializers

from apps.notification.models import GlobalNotification, RentalNotification, GlobalNotificationConfirm


class GlobalNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalNotification
        exclude = ['updated_at']


class GlobalNotificationConfirmSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='notification.text', read_only=True)
    image = serializers.CharField(source='notification.image.url', read_only=True)
    recipient = serializers.CharField(source='notification.user', read_only=True)

    class Meta:
        model = GlobalNotificationConfirm
        exclude = ['updated_at', 'notification', 'user']


class RentalNotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='rental_history.product.name')  # 상품 이름
    product_image = serializers.SerializerMethodField()  # 상품 이미지
    borrower = serializers.CharField(source='rental_history.borrower.nickname')  # 빌리는 사람
    lender = serializers.CharField(source='rental_history.product.lender.nickname')  # 판매자
    rental_date = serializers.DateTimeField(source='rental_history.rental_date')  # 대여일
    return_date = serializers.DateTimeField(source='rental_history.return_date')  # 반납일
    status = serializers.CharField(source='rental_history.status')  # 상태 : 대여신청, 대여수락, 대여중, 반납

    class Meta:
        model = RentalNotification
        fields = [
            'id',
            'recipient',
            'product_name',
            'product_image',
            'borrower',
            'lender',
            'rental_date',
            'return_date',
            'status',
            'created_at',
        ]

    def get_product_image(self, obj):
        product_images = obj.rental_history.product.images.first()
        if product_images:
            return product_images.image.url  # 이미지의 URL을 리턴
        return None  # 이미지가 없을 경우 None을 리턴
