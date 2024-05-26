from django.db import models

from apps.common.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Style(BaseModel):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self) -> str:
        return self.name
