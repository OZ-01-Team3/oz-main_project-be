from django.shortcuts import render
from rest_framework import generics, permissions

from apps.mypage.serializers import MyProductSerializer
from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class MyProductListView(generics.ListAPIView):
    serializer_class = MyProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> Product:
        lender = self.request.user
        return Product.objects.filter(lender=lender).order_by('-created_at')
