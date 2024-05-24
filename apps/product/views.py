from typing import Any

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from requests import Response
from rest_framework import generics, permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from apps.product.models import Product, ProductImage, RentalHistory
from apps.product.permissions import IsLenderOrReadOnly
from apps.product.serializers import (
    ProductImageSerializer,
    ProductSerializer,
    RentalHistorySerializer,
)


# @method_decorator(cache_page(60 * 60 * 2), name="dispatch")
class ProductViewSet(viewsets.ModelViewSet[Product]):
    # queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsLenderOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "product_category", "condition", "size"]
    search_fields = ["name", "lender__nickname"]
    ordering_fields = ["created_at", "rental_fee", "views"]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer: BaseSerializer[Product]) -> None:
        serializer.save(lender=self.request.user)

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.all().order_by("-created_at")


class RentalHistoryViewSet(viewsets.ModelViewSet[RentalHistory]):
    queryset = RentalHistory.objects.all()
    serializer_class = RentalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["product__name", "lender"]
    ordering_fields = ["rental_date", "return_date"]

    def get_queryset(self) -> QuerySet[RentalHistory]:
        # 반납 상태가 아직 False인 대여 기록만 반환하도록 필터링
        queryset = super().get_queryset()
        return queryset.filter(returned=False)

    # 대여 상태 변경을 위한 엔드포인트 추가
    # def return_rental(self, request, *args, **kwargs):
    #     rental = self.get_object()
    #     rental.returned = True
    #     rental.save()
    #     return Response({"message": "반납이 완료 되었습니다."}, status=status.HTTP_200_OK)
    #
    # # 대여 상태 변경을 위한 라우트 추가
    # def return_rental(self, request, *args, **kwargs):
    #     return self.return_rental_record(request, *args, **kwargs)
