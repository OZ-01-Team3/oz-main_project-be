from rest_framework import generics, permissions

from apps.category.models import Category, Style
from apps.category.serializers import CategorySerializer, StyleSerializer


class CategoryListView(generics.ListAPIView[Category]):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class StyleListView(generics.ListAPIView[Style]):
    queryset = Style.objects.all()
    serializer_class = StyleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
