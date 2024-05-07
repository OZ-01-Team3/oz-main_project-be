from rest_framework import serializers

from apps.category.models import Category


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ("id", "name")
