import uuid
from django.db import models
from apps.common.models import BaseModel
from apps.common.utils import uuid4_generator

# class ProductCategory(models.Model):
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name
#
# class StyleCategory(models.Model):
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name
# def load_initial_data(apps, schema_editor):
#     ProductCategory = apps.get_model(app_label='product', model_name='ProductCategory')
#     StyleCategory = apps.get_model(app_label='product', model_name='StyleCategory')
#
#     # 카테고리 추가
#     ProductCategory.objects.bulk_create([
#         ProductCategory(name='전체'),
#         ProductCategory(name='아우터'),
#         ProductCategory(name='상의'),
#         ProductCategory(name='하의'),
#         ProductCategory(name='잡화'),
#         ProductCategory(name='신발'),
#     ])
#
#     # 스타일 추가
#     StyleCategory.objects.bulk_create([
#         StyleCategory(name='캐쥬얼'),
#         StyleCategory(name='패미닌'),
#         StyleCategory(name='아메카지'),
#         StyleCategory(name='모던'),
#         StyleCategory(name='하이틴'),
#         StyleCategory(name='Y2K'),
#         StyleCategory(name='프레피룩'),
#         StyleCategory(name='유니섹스'),
#         StyleCategory(name='스트릿'),
#         StyleCategory(name='매니쉬'),
#         StyleCategory(name='스포티'),
#         StyleCategory(name='애스닉'),
#         StyleCategory(name='그런지'),
#         StyleCategory(name='테크웨어'),
#         StyleCategory(name='밀리터리'),
#     ])
#
#
# class ProductCategory(models.Model):
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name
#
#
# class StyleCategory(models.Model):
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name


class Product(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    user = models.ForeignKey("user.Account", on_delete=models.CASCADE, related_name="product")
    # brand = models.ForeignKey(on_delete=models.SET_NULL, null=True)  # 브랜드
    condition = models.TextField()  # 옷 상태
    purchasing_price = models.IntegerField()  # 구매 당시 가격
    rental_fee = models.IntegerField()  # 대여 비용
    size = models.CharField(max_length=10)  # 사이즈
    views = models.IntegerField(default=0)  # 조회수
    product_category = models.ForeignKey("category.Category", on_delete=models.CASCADE, related_name="product")
    #style_category = models.ManyToManyField(StyleCategory)
    status = models.BooleanField(default=True)  # 대여 가능 여부

    def __str__(self) -> str:
        return self.name


# def upload_to_s3_product(instance: models.Model, filename: str) -> str:
#     # 파일명은 랜덤한 8자리의 문자열과 업로드한 파일이름을 조합해서 만듦(유일성 보장)
#     return f"images/product/{uuid4_generator(length=8)} + {filename}"


# class ProductImage(BaseModel):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     image = models.ImageField(upload_to=upload_to_s3_product)