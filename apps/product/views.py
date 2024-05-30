from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, UpdateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.product.models import Product, RentalHistory
from apps.product.permissions import IsLenderOrReadOnly
from apps.product.serializers import ProductSerializer, RentalHistorySerializer
from apps.product.utils import clear_cache, get_or_set_cache

CACHE_TIME = 60 * 60 * 24
PRODUCT_KEY = "products_list"


class ProductViewSet(viewsets.ModelViewSet[Product]):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsLenderOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "product_category", "condition", "size", "styles"]
    search_fields = ["name", "lender__nickname"]
    ordering_fields = ["created_at", "rental_fee", "views", "likes"]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self) -> Any:
        queryset = Product.objects.all().order_by("-created_at")
        cached_queryset = get_or_set_cache(PRODUCT_KEY, queryset, CACHE_TIME)
        # queryset = get_cache(PRODUCT_KEY)
        # if not queryset:
        #     queryset = Product.objects.all().order_by("-created_at")
        #     set_cache(PRODUCT_KEY, queryset, CACHE_TIME)
        return cached_queryset

    def perform_create(self, serializer: BaseSerializer[Product]) -> None:
        serializer.save(lender=self.request.user)
        clear_cache(PRODUCT_KEY)

    def perform_update(self, serializer: BaseSerializer[Product]) -> None:
        serializer.save()
        clear_cache(PRODUCT_KEY)

    def perform_destroy(self, instance: Product) -> None:
        instance.delete()
        clear_cache(PRODUCT_KEY)


class RentalHistoryBorrowerView(ListCreateAPIView[RentalHistory]):
    serializer_class = RentalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[RentalHistory]:
        return RentalHistory.objects.filter(borrower=self.request.user)  # type: ignore

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = {
            "borrower_id": request.data.get("borrower_id"),
            "product": request.data.get("product"),
            "status": request.data.get("status"),
        }
        if RentalHistory.objects.filter(**data).exists():
            return Response({"msg": "이미 상품에 대한 대여 내역이 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        data["rental_date"] = request.data.get("rental_date")
        data["return_date"] = request.data.get("return_date")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RentalHistoryLenderView(ListAPIView[RentalHistory]):
    serializer_class = RentalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[RentalHistory]:
        queryset = RentalHistory.objects.filter(product__lender=self.request.user)  # type: ignore
        return queryset

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RentalHistoryUpdateView(UpdateAPIView[RentalHistory]):
    serializer_class = RentalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[RentalHistory]:
        queryset = RentalHistory.objects.all()
        return queryset
