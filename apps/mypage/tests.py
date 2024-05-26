from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.category.models import Category
from apps.product.models import Product
from apps.user.models import Account


class MyProductTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("my-products")
        data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
        }
        self.user = Account.objects.create_user(**data)
        self.category = Category.objects.create(name="test category")
        self.product = Product.objects.create(
            name="test product",
            lender=self.user,
            brand="test brand",
            condition="good",
            purchase_date="2024-01-01",
            purchase_price=10000,
            rental_fee=1000,
            size="xs",
            product_category=self.category,
        )

    def test_get_my_products(self) -> None:
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
