from typing import Any

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.contrib import django_filters
from requests import Response
from rest_framework import generics, permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from apps.product.models import Product, RentalHistory, ProductImage
from apps.product.permissions import IsLenderOrReadOnly
from apps.product.serializers import ProductSerializer, RentalHistorySerializer, ProductImageSerializer


# @method_decorator(cache_page(60 * 60 * 2), name="dispatch")
class ProductViewSet(viewsets.ModelViewSet[Product]):
    # queryset = Product.objects.all().prefetch_related('images')
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsLenderOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "product_category", "condition", "size", "region"]
    search_fields = ["name", "lender__nickname"]
    ordering_fields = ["created_at", "rental_fee", "views"]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer: BaseSerializer[Product]) -> None:
        print("req!", self.request.META)
        print("cookie!", self.request.COOKIES)
        print("csrf!", self.request.COOKIES["csrftoken"])
        serializer.save(lender=self.request.user)

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.all().order_by("-created_at")

    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     search_name = self.request.query_params.get("name")
    #     if search_name:
    #         qs = qs.filter(name__icontains=search_name)
    #         return qs

    # @method_decorator(cache_page(60 * 60 * 2))
    # def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
    #     queryset = self.filter_queryset(self.get_queryset())
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)


class ProductImageDeleteView(generics.DestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer = ProductImageSerializer





class ProductImageCreateView(generics.CreateAPIView):
    pass


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


# class SearchProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     permission_classes = [AllowAny]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ProductFilter
