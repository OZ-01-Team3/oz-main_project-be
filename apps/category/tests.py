from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.category.models import Category


class CategoryModelTest(TestCase):
    def setUp(self) -> None:
        Category.objects.create(name="test_category1")
        Category.objects.create(name="test_category2")

    def test_get_all_categories(self) -> None:
        """
        모든 카테고리 조회
        """
        client = APIClient()
        url = reverse("category-list")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data.get("count"), 2)
        self.assertEqual(len(response.data), 2)
