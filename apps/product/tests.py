# from django.test import TestCase
# from django.urls import reverse
# from mypyc.irbuild.builder import IRBuilder
# from mypyc.irbuild.builder.IRBuilder import self
# from rest_framework import status
# from rest_framework.test import APIClient
#
# from apps.product.models import Product
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.category.models import Category, Style
from apps.product.models import Product, RentalHistory
from apps.user.models import Account

# class ProductListAPITest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.product1 = Product.objects.create(
#             name='Product 1',
#             user_id=1,
#             brand='Brand 1',
#             condition='Good',
#             purchasing_price=100000,
#             rental_fee=5000,
#             size='L',
#             views=100,
#             product_category_id=1,
#             style_category_id=1,
#             status=True
#         )
#         self.product2 = Product.objects.create(
#             name='Product 2',
#             user_id=2,
#             brand='Brand 2',
#             condition='Bad',
#             purchasing_price=80000,
#             rental_fee=4000,
#             size='S',
#             views=0,
#             product_category_id=2,
#             style_category_id=2,
#             status=False
#         )
#
#         # API 호출
#
#     response = self.client.get('/api/products/')
#
#     # 응답 확인
#     self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     # 응답 데이터의 길이가 2인지 확인 (2개의 상품이 반환되어야 함)
#     self.assertEqual(len(response.data), 2)
#
#     # 상품의 모든 필드들을 확인
#     self.assertEqual(response.data[0]['name'], 'Product 1')
#     self.assertEqual(response.data[0]['user'], 1)
#     self.assertEqual(response.data[0]['brand'], 'Brand 1')
#     self.assertEqual(response.data[0]['condition'], 'New')
#     self.assertEqual(response.data[0]['purchasing_price'], 10000)
#     self.assertEqual(response.data[0]['rental_fee'], 5000)
#     self.assertEqual(response.data[0]['size'], 'M')
#     self.assertEqual(response.data[0]['views'], 0)
#     self.assertEqual(response.data[0]['product_category_id'], 1)
#     self.assertEqual(response.data[0]['style_category_id'], 1)
#     self.assertEqual(response.data[0]['status'], True)
#
#     self.assertEqual(response.data[1]['name'], 'Product 2')
#     self.assertEqual(response.data[1]['user'], 2)
#     self.assertEqual(response.data[1]['brand'], 'Brand 2')
#     self.assertEqual(response.data[1]['condition'], 'Used')
#     self.assertEqual(response.data[1]['purchasing_price'], 8000)
#     self.assertEqual(response.data[1]['rental_fee'], 4000)
#     self.assertEqual(response.data[1]['size'], 'L')
#     self.assertEqual(response.data[1]['views'], 0)
#     self.assertEqual(response.data[1]['product_category_id'], 2)
#     self.assertEqual(response.data[1]['style_category_id'], 2)
#     self.assertEqual(response.data[1]['status'], True)
# def test_product_list_api_view(self):
#     url = reverse("product_list")
#     response = self.client.get(url)
#     self.assertEqual(response.status_code, status.HTTP_200_OK)
#     self.assertEqual(len(response.data), Product.objects.count())
#
# def test_product_create_api_view(self):
#     url = reverse("product_create")
#     response = self.client.post(url, self.product_data, format="json")
#     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
# def test_product_detail_api_view(self):
#     url = reverse("product_detail", args=[self.product.pk])
#     response = self.client.get(url)
#     self.assertEqual(response.status_code, status.HTTP_200_OK)
#     #내가 셋업에 만든 상품이랑 이 뷰에서 조회 하고자 하는 상품의 데이터가 일치 하는 지를 확인해야함
#


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
            "product": self.product.uuid,
            "rental_date": timezone.now(),
            "return_date": timezone.now() + timedelta(days=3),
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
            "product": history.product.uuid,
            "rental_date": history.rental_date.isoformat(),
            "return_date": history.return_date.isoformat(),  # type: ignore
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
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("return_date").split("T")[0], data["return_date"].date().isoformat())
