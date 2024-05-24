import uuid
from typing import Any

from django.db import models

from apps.common.models import BaseModel
from apps.common.utils import uuid4_generator
from apps.user.models import Account


class Product(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    lender = models.ForeignKey("user.Account", on_delete=models.CASCADE, related_name="products")
    # brand = models.ForeignKey(on_delete=models.SET_NULL, null=True)  # 브랜드
    brand = models.CharField(max_length=20, default="None")
    condition = models.TextField()  # 옷 상태
    description = models.TextField(null=True, blank=True)
    purchase_date = models.DateField()
    purchase_price = models.IntegerField()  # 구매 당시 가격
    rental_fee = models.IntegerField()  # 대여 비용
    size = models.CharField(max_length=10)  # 사이즈
    views = models.IntegerField(default=0)  # 조회수
    product_category = models.ForeignKey("category.Category", on_delete=models.CASCADE, related_name="products")
    # style_category = models.ManyToManyField(StyleCategory)
    status = models.BooleanField(default=True)  # 대여 가능 여부
    amount = models.IntegerField(default=1)
    region = models.CharField(max_length=30, default="None")

    def __str__(self) -> str:
        return self.name

    # @property
    # def current_rental_record(self):
    #     return self.rental_records.filter(return_date__isnull=True).first()


def upload_to_s3_product(instance: models.Model, filename: str) -> str:
    # 파일명은 랜덤한 8자리의 문자열과 업로드한 파일이름을 조합해서 만듦(유일성 보장)
    return f"images/product/{uuid4_generator(length=8)} + {filename}"


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=upload_to_s3_product)

    def get_image_url(self) -> Any | None:
        if self.image and hasattr(self.image, "url"):
            return self.image.url
        return None


class RentalHistory(BaseModel):
    STATUS_CHOICE = [
        ("REQUEST", "request"),  # 대여 요청 상태
        ("ACCEPT", "accept"),  # 대여 승인 상태
        ("RETURNED", "returned"),  # 상품 반납 완료 상태
        ("BORROWING", "borrowing"),  # 상품 대여 중 상태
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Account, on_delete=models.CASCADE)
    rental_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)  # 대여 반납일
    status = models.CharField(choices=STATUS_CHOICE, default="REQUEST", max_length=10)

    def __str__(self) -> str:
        return f"{self.product} - Rented by {self.product.lender}"
