from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from apps.category.models import Category


class CategoryModelTest(TestCase):
    def setUp(self):
        Category.objects.create(name="test_category1")
        Category.objects.create(name="test_category2")

    def test_get_all_categories(self) -> None:
        """
        모든 카테고리 조회
        """
        url = reverse("category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
