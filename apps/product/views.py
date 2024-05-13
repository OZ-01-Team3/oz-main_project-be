from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny  # IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.product.models import Product
from apps.product.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet[Product]):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer: BaseSerializer[Product]) -> None:
        product = serializer.save(user=self.request.user)
