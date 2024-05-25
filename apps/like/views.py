from django.db import transaction, IntegrityError
from django.db.models import QuerySet, F
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

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
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permissions_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def perform_create(self, serializer: LikeSerializer) -> None:
        product_id = self.kwargs.get("pk")
        product = Product.objects.get(pk=product_id)

        try:
            with transaction.atomic():
                Product.objects.filter(pk=product_id).update(likes=F("likes") + 1)
                serializer.save(user=self.request.user, product=product)
                # product.likes = F("likes") + 1
                # product.save(update_fields=["likes"])
        except IntegrityError:
            raise ValidationError("Already liked this product.")


class LikeDestroyView(generics.DestroyAPIView):
    # serializer_class = LikeSerializer
    permissions_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def get_object(self) -> QuerySet[Like]:
        product_id = self.kwargs.get("pk")
        return Like.objects.filter(user=self.request.user, product_id=product_id)

    @transaction.atomic
    def perform_destroy(self, instance):
        product_id = self.kwargs.get("pk")
        Product.objects.filter(pk=product_id).update(likes=F("likes") + 1)
        # product.likes = F("likes") - 1
        # product.save(update_fields=["likes"])
        instance.delete()
