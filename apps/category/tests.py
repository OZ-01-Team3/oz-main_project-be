from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.category.models import Category, Style


class CategoryListTest(TestCase):
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


class StyleListTest(TestCase):
    def setUp(self) -> None:
        Style.objects.create(name="test_style1")
        Style.objects.create(name="test_style2")

    def test_get_all_styles(self) -> None:
        client = APIClient()
        url = reverse("style-list")
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
