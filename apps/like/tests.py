from django.urls import reverse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.category.models import Category
from apps.like.models import Like
from apps.product.models import Product
from apps.user.models import Account


class TestLikeListCreateView(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("likes")
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

    def test_list_likes(self) -> None:
        self.client.force_authenticate(user=self.user)
        Like.objects.create(user=self.user, product=self.product)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get("count"), 1)

    def test_create_like(self) -> None:
        self.client.force_authenticate(user=self.user)
        data = {"product_id": self.product.uuid}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, product=self.product).exists())

    def test_create_like_without_product_id(self) -> None:
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Like.objects.filter(user=self.user, product=self.product).exists())

    def test_create_like_already_exists(self) -> None:
        self.client.force_authenticate(user=self.user)
        Like.objects.create(user=self.user, product=self.product)
        data = {"product_id": self.product.uuid}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data, ["Already liked this product."])

    def test_create_list_without_login(self) -> None:
        data = {"product_id": self.product.uuid}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLikeDestroyView(APITestCase):
    def setUp(self) -> None:
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
            likes=1,
        )
        self.like = Like.objects.create(user=self.user, product=self.product)
        self.url = reverse("like_delete", kwargs={"pk": self.product.pk})

    def test_delete_like(self) -> None:
        self.client.force_authenticate(user=self.user)
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(user=self.user, product=self.product).exists())

    # def test_like_count_decreased(self) -> None:
    #     self.client.force_authenticate(user=self.user)
    #     initial_count = self.product.likes
    #     res = self.client.delete(self.url)
    #     self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
    #     self.assertEqual(self.product.likes, initial_count - 1)

    def test_delete_like_not_found(self) -> None:
        self.client.force_authenticate(user=self.user)
        self.like.delete()
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_like_by_other_user(self) -> None:
        data = {
            "email": "otuser@email.com",
            "password": "fels3570",
            "nickname": "dfk",
            "phone": "1234",
        }
        other_user = Account.objects.create_user(**data)
        self.client.force_authenticate(other_user)
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class TestPermission(APITestCase):
    pass
