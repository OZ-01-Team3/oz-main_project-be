from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.like.models import Like
from apps.like.permissions import IsUserOrReadOnly
from apps.like.serializers import LikeSerializer
from apps.product.models import Product


class LikeListView(generics.ListAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Like]:
        user = self.request.user
        return Like.objects.filter(user=user).order_by("-created_at")


class LikeCreateView(generics.CreateAPIView):
    serializer_class = LikeSerializer
    permissions_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def perform_create(self, serializer: LikeSerializer) -> None:
        product_id = self.kwargs.get("pk")
        product = Product.objects.get(pk=product_id)
        serializer.save(user=self.request.user, product=product)


class LikeDestroyView(generics.DestroyAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def get_queryset(self) -> QuerySet[Like]:
        product_id = self.kwargs.get("pk")
        return Like.objects.filter(user=self.request.user, pk=product_id)
