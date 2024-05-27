from django.shortcuts import render
from rest_framework import generics, permissions

from apps.mypage.models import InterestedStyle
from apps.mypage.serializers import MyProductSerializer
from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class MyProductListView(generics.ListAPIView):
    serializer_class = MyProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> Product:
        lender = self.request.user
        return Product.objects.filter(lender=lender).order_by('-created_at')


# class InterestedStyleProductListView(generics.ListAPIView):
#     serializer_class = ProductSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self) -> Product:
#         user = self.request.user
#         interested_styles = InterestedStyle.objects.filter(user=user).values_list('styles', flat=True)
#         return Product.objects.filter(styles__in=interested_styles).distinct().order_by('-created_at')


# class InterestedStyleUpdateView(generics.UpdateAPIView):
#     queryset = InterestedStyle.objects.all()
#     serializer_class = InterestedStyleSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_object(self) -> InterestedStyle:
#         user = self.request.user
#         obj, created = InterestedStyle.objects.get_or_create(user=user)
#         return obj
