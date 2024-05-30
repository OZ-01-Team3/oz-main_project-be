from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APIRequestFactory,
    APITestCase,
    force_authenticate,
)
from rest_framework_simplejwt.tokens import AccessToken

from apps.category.models import Category, Style
from apps.product.models import Product, ProductImage, RentalHistory
from apps.product.permissions import IsLenderOrReadOnly
from apps.product.serializers import ProductImageSerializer, ProductSerializer
from apps.product.views import ProductViewSet
from apps.user.models import Account


class RentalHistoryTestBase(APITestCase):
    def setUp(self) -> None:
        self.borrower = Account.objects.create_user(
            email="test1@example.com", nickname="test_borrower", password="password1234@", phone="010-2211-1111"
        )
        self.lender = Account.objects.create_user(
            email="test2@example.com", nickname="test_lender", password="password1234@", phone="010-2211-1112"
        )
        self.category = Category.objects.create(name="test_category")
        self.styles = Style.objects.create(name="test_style_tag")
        self.product = Product.objects.create(
            name="testproduct",
            lender=self.lender,
            condition="testcondition",
            purchase_date=timezone.now(),
            purchase_price=50000,
            rental_fee=5000,
            size="XL",
            product_category=self.category,
        )
        self.product.styles.add(self.styles)
        self.token = AccessToken.for_user(self.borrower)


class RentalHistoryBorrowerViewTests(RentalHistoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("borrowed_rental_history")

    def test_대여자가_정상적인_물품_대여신청을_했을때(self) -> None:
        data = {
            "borrower_id": self.borrower.id,
            "product": self.product.uuid,
            "rental_date": timezone.now(),
            "return_date": timezone.now() + timedelta(days=3),
            "status": "REQUEST",
        }
        response = self.client.post(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RentalHistory.objects.count(), 1)
        self.assertEqual(response.data.get("product_info")["uuid"], str(self.product.uuid))
        self.assertEqual(response.data.get("borrower_nickname"), self.borrower.nickname)
        self.assertEqual(response.data.get("status"), "대여 요청")

    def test_이미_대여중인_상품을_대여하려고_시도하는경우_테스트(self) -> None:
        history = RentalHistory.objects.create(
            product=self.product,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )
        self.assertEqual(RentalHistory.objects.count(), 1)
        data = {
            "borrower_id": int(self.borrower.id),
            "product": str(history.product.uuid),
            "rental_date": history.rental_date.isoformat(),
            "return_date": history.rental_date.isoformat(),
            "status": history.status,
        }
        response = self.client.post(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_생성된_대여내역_정상적인_조회_테스트(self) -> None:
        # given
        lender2 = Account.objects.create_user(
            email="test3@example.com", nickname="test_lender2", password="password1234@", phone="010-2211-1113"
        )
        product2 = Product.objects.create(
            name="testproduct2",
            lender=lender2,
            condition="testcondition",
            purchase_date=timezone.now(),
            purchase_price=40000,
            rental_fee=3000,
            size="M",
            product_category=self.category,
        )
        RentalHistory.objects.create(
            product=self.product,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )
        RentalHistory.objects.create(
            product=product2,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )

        response = self.client.get(self.url, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), RentalHistory.objects.count())
        self.assertEqual(response.data[0]["product_info"]["uuid"], str(self.product.uuid))
        self.assertEqual(response.data[1]["product_info"]["uuid"], str(product2.uuid))
        self.assertEqual(response.data[0]["borrower_nickname"], self.borrower.nickname)
        self.assertEqual(response.data[1]["borrower_nickname"], self.borrower.nickname)


class RentalHistoryLenderViewTests(RentalHistoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("lending_rental_history")
        self.lender2 = Account.objects.create_user(
            email="test3@example.com", nickname="test_lender2", password="password1234@", phone="010-2211-1113"
        )
        self.product2 = Product.objects.create(
            name="testproduct2",
            lender=self.lender2,
            condition="testcondition",
            purchase_date=timezone.now(),
            purchase_price=40000,
            rental_fee=3000,
            size="M",
            product_category=self.category,
        )
        self.history1 = RentalHistory.objects.create(
            product=self.product,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )
        self.history2 = RentalHistory.objects.create(
            product=self.product2,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )

    def test_lender의_판매내역_조회_테스트(self) -> None:
        self.token = AccessToken.for_user(self.lender)

        response = self.client.get(self.url, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["product_info"]["uuid"], str(self.product.uuid))
        self.assertEqual(response.data[0]["borrower_nickname"], self.borrower.nickname)
        self.assertEqual(response.data[0]["lender_nickname"], self.lender.nickname)

    def test_lender2의_판매내역_조회_테스트(self) -> None:
        self.token = AccessToken.for_user(self.lender2)

        response = self.client.get(self.url, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["product_info"]["uuid"], str(self.product2.uuid))
        self.assertEqual(response.data[0]["borrower_nickname"], self.borrower.nickname)
        self.assertEqual(response.data[0]["lender_nickname"], self.lender2.nickname)


class RentalHistoryUpdateViewTests(RentalHistoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.history = RentalHistory.objects.create(
            product=self.product,
            borrower=self.borrower,
            rental_date=timezone.now(),
            return_date=timezone.now() + timedelta(days=3),
        )
        self.url = reverse("rental_history_update", kwargs={"pk": self.history.pk})

    def test_대여요청에서_상태_업데이트_테스트(self) -> None:
        data = {"status": "ACCEPT"}
        response = self.client.patch(self.url, data=data, headers={"Authorization": f"Bearer {self.token}"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("status"), "대여 요청 수락")

    def test_대여날짜_변경_테스트(self) -> None:
        data = {"return_date": timezone.now() + timedelta(days=4)}

        response = self.client.patch(self.url, data=data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("return_date").split("T")[0], data["return_date"].date().isoformat())


class ProductModelTest(TestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(email="test@example.com", password="password")
        self.category = Category.objects.create(name="category1")
        self.style = Style.objects.create(name="style1")
        self.data = {
            "name": "product1",
            "lender": self.user,
            "brand": "brand",
            "condition": "condition",
            "purchase_date": "2024-05-01",
            "purchase_price": 100000,
            "rental_fee": 10000,
            "size": "m",
            "product_category": self.category,
            "amount": 1,
            "region": "Seoul",
        }
        self.product = Product.objects.create(**self.data)
        self.product.styles.add(self.style)

    def test_create_product(self) -> None:
        self.assertEqual(self.product.name, self.data["name"])
        self.assertEqual(self.product.lender, self.data["lender"])
        self.assertEqual(self.product.brand, self.data["brand"])
        self.assertEqual(self.product.condition, self.data["condition"])
        self.assertEqual(self.product.purchase_date, self.data["purchase_date"])
        self.assertEqual(self.product.purchase_price, self.data["purchase_price"])
        self.assertEqual(self.product.rental_fee, self.data["rental_fee"])
        self.assertEqual(self.product.size, self.data["size"])
        self.assertEqual(self.product.product_category, self.data["product_category"])
        self.assertTrue(self.product.status)
        self.assertEqual(self.product.amount, self.data["amount"])
        self.assertEqual(self.product.region, self.data["region"])
        self.assertIn(self.style, self.product.styles.all())

    def test_create_product_image(self) -> None:
        image = SimpleUploadedFile("test_product_image.jpg", b"content", content_type="image/jpeg")
        product_image = ProductImage.objects.create(product=self.product, image=image)
        self.assertEqual(product_image.product, self.product)
        self.assertIsNotNone(product_image.get_image_url())


class ProductSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(email="test@example.com", password="password")
        self.category = Category.objects.create(name="category1")
        self.style = Style.objects.create(name="style1")
        data = {
            "name": "product1",
            "lender": self.user,
            "brand": "brand",
            "condition": "condition",
            "purchase_date": "2024-05-01",
            "purchase_price": 100000,
            "rental_fee": 10000,
            "size": "m",
            "product_category": self.category,
            "amount": 1,
            "region": "Seoul",
        }
        self.product = Product.objects.create(**data)
        self.product.styles.add(self.style)
        self.factory = APIRequestFactory()

    def test_product_serializer(self) -> None:
        request = self.factory.get("/api/products/")
        request.user = self.user
        serializer = ProductSerializer(instance=self.product, context={"request": request})
        data = serializer.data

        self.assertEqual(data["name"], self.product.name)
        self.assertEqual(data["lender"]["email"], self.user.email)
        self.assertEqual(data["brand"], self.product.brand)
        self.assertEqual(data["condition"], self.product.condition)
        self.assertEqual(data["purchase_date"], self.product.purchase_date)
        self.assertEqual(data["purchase_price"], self.product.purchase_price)
        self.assertEqual(data["rental_fee"], self.product.rental_fee)
        self.assertEqual(data["size"], self.product.size)
        self.assertEqual(data["product_category"], self.product.product_category.name)
        self.assertEqual(data["status"], self.product.status)
        self.assertEqual(data["amount"], self.product.amount)
        self.assertEqual(data["region"], self.product.region)


class ProductImageSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(email="test@example.com", password="password")
        self.category = Category.objects.create(name="category1")
        self.style = Style.objects.create(name="style1")
        data = {
            "name": "product1",
            "lender": self.user,
            "brand": "brand",
            "condition": "condition",
            "purchase_date": "2024-05-01",
            "purchase_price": 100000,
            "rental_fee": 10000,
            "size": "m",
            "product_category": self.category,
            "amount": 1,
            "region": "Seoul",
        }
        self.product = Product.objects.create(**data)
        self.product.styles.add(self.style)
        self.image = SimpleUploadedFile("test_product_image.jpg", b"content", content_type="image/jpg")

    def test_product_image_serializer(self) -> None:
        image = ProductImage.objects.create(product=self.product, image=self.image)
        serializer = ProductImageSerializer(image)
        data = serializer.data
        self.assertEqual(data["id"], image.id)
        self.assertIsNotNone(data["image"])


class ProductViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = Account.objects.create_user(email="test@example.com", password="password")
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="category1")
        self.style = Style.objects.create(name="style1")
        self.data = {
            "name": "product1",
            "lender": self.user,
            "brand": "brand",
            "condition": "condition",
            "purchase_date": "2024-05-01",
            "purchase_price": 100000,
            "rental_fee": 10000,
            "size": "m",
            "product_category": self.category,
            "amount": 1,
            "region": "Seoul",
        }

    def test_list_products(self) -> None:
        Product.objects.create(**self.data)
        res = self.client.get(reverse("product-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("count"), 1)

    def test_create_product(self) -> None:
        url = reverse("product-list")
        res = self.client.post(url, data=self.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.get().name, self.data["name"])

    def test_update_product(self) -> None:
        product = Product.objects.create(**self.data)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        update_data = {"name": "product2"}
        res = self.client.patch(url, update_data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Product.objects.get().name, update_data["name"])

    def test_delete_product(self) -> None:
        product = Product.objects.create(**self.data)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)


class ProductPermissionTest(TestCase):
    def setUp(self) -> None:
        self.user1 = Account.objects.create_user(email="user1@test.com", password="password", nickname="user1")
        self.user2 = Account.objects.create_user(email="user2@test.com", password="password", nickname="user2")
        self.product = Product.objects.create(
            name="product1",
            lender=self.user1,
            brand="brand",
            condition="new",
            purchase_date="2022-01-01",
            purchase_price=100000,
            rental_fee=5000,
            size="M",
            product_category=Category.objects.create(name="category1"),
            status=True,
            amount=1,
            region="Seoul",
        )
        self.factory = APIRequestFactory()

    def test_permission_as_lender(self) -> None:
        request = self.factory.put(f"/api/product/{self.product.pk}/")
        force_authenticate(request, user=self.user1)
        request.user = self.user1
        view = ProductViewSet()
        permission = IsLenderOrReadOnly()
        self.assertTrue(permission.has_permission(request, view))
        self.assertTrue(permission.has_object_permission(request, view, self.product))

    def test_permission_as_other_user(self) -> None:
        request = self.factory.put(f"/api/product/{self.product.pk}/")
        force_authenticate(request, user=self.user2)
        request.user = self.user2
        view = ProductViewSet()
        permission = IsLenderOrReadOnly()
        self.assertTrue(permission.has_permission(request, view))
        self.assertFalse(permission.has_object_permission(request, view, self.product))

    def test_permission_as_unauthenticated(self) -> None:
        request = self.factory.put(f"/api/product/{self.product.pk}/")
        request.user = AnonymousUser()
        view = ProductViewSet()
        permission = IsLenderOrReadOnly()
        self.assertTrue(permission.has_permission(request, view))
        self.assertFalse(permission.has_object_permission(request, view, self.product))
