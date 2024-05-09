import uuid
from django.db import models
from apps.common.models import BaseModel
from apps.common.utils import uuid4_generator


class Product(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    #brand = models.ForeignKey(on_delete=models.SET_NULL, null=True)  # 브랜드
    condition = models.TextField()  # 옷 상태
    purchasing_price = models.IntegerField()  # 구매 당시 가격
    rental_fee = models.IntegerField()  # 대여 비용
    size = models.CharField(max_length=10)  # 사이즈
    views = models.IntegerField(default=0)  # 조회수
    #product_category_id = models.ForeignKey()
    #style_category_id = models.ManyToManyField()
    status = models.BooleanField(default=True)  # 대여 가능 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 등록일
    updated_at = models.DateTimeField(auto_now=True)  # 수정일


    def __str__(self):
        return self.name


def upload_to_s3_product(instance: models.Model, filename: str) -> str:
    # 파일명은 랜덤한 8자리의 문자열과 업로드한 파일이름을 조합해서 만듦(유일성 보장)
    return f"images/product/{uuid4_generator(length=8)} + {filename}"


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_to_s3_product)