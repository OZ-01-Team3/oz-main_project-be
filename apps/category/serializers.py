from rest_framework import serializers

from apps.category.models import Category, Style


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ("id", "name")


class StyleSerializer(serializers.ModelSerializer[Style]):
    class Meta:
        model = Style
        fields = ("id", "name")
