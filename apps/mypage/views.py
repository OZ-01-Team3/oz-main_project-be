from django.db.models import QuerySet
from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.mypage.serializers import MyProductSerializer
from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from apps.user.models import Account


class MyProductListView(generics.ListAPIView[Product]):
    serializer_class = MyProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Product]:
        lender = self.request.user
        if not isinstance(lender, Account):
            raise PermissionDenied("You must be logged in to view your likes.")
        return Product.objects.filter(lender=lender).order_by("-created_at")
