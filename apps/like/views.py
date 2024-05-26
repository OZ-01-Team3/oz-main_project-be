from typing import Union
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import F, QuerySet
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.serializers import BaseSerializer

from apps.like.models import Like
from apps.like.permissions import IsUserOrReadOnly
from apps.like.serializers import LikeSerializer
from apps.product.models import Product
from apps.user.models import Account

# class LikeListView(generics.ListAPIView):
#     serializer_class = LikeSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self) -> QuerySet[Like]:
#         user = self.request.user
#         return Like.objects.filter(user=user).order_by("-created_at")


class LikeListCreateView(generics.ListCreateAPIView[Like]):
    serializer_class = LikeSerializer
    permissions_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def get_queryset(self) -> QuerySet[Like]:
        user = self.request.user
        if not isinstance(user, Account):
            raise PermissionDenied("You must be logged in to view your likes.")
        return Like.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer: BaseSerializer[Like]) -> None:
        product_id = self.request.data.get("product_id")
        # product = Product.objects.get(pk=product_id)
        if not product_id:
            raise ValidationError("You must provide a product ID.")

        try:
            with transaction.atomic():
                serializer.save(user=self.request.user, product_id=product_id)
                Product.objects.filter(pk=product_id).update(likes=F("likes") + 1)
                # product.likes = F("likes") + 1
                # product.save(update_fields=["likes"])
        except IntegrityError:
            raise ValidationError("Already liked this product.")


class LikeDestroyView(generics.DestroyAPIView[Like]):
    # serializer_class = LikeSerializer
    permissions_classes = [permissions.IsAuthenticated, IsUserOrReadOnly]

    def get_object(self) -> Like:
        product_id = self.kwargs.get("pk")
        user = self.request.user if isinstance(self.request.user, Account) else None
        # like = Like.objects.filter(user=user, product_id=product_id).first()
        # if not like:
        #     raise NotFound("No Like matches the given query.")
        # return like
        try:
            like = Like.objects.get(user=user, product_id=product_id)
            return like
        except Like.DoesNotExist:
            raise NotFound("No Like matches the given query.")

    @transaction.atomic
    def perform_destroy(self, instance: Like) -> None:
        product_id = self.kwargs.get("pk")
        if instance:
            instance.delete()
            Product.objects.filter(pk=product_id).update(likes=F("likes") - 1)
            # product.likes = F("likes") - 1
            # product.save(update_fields=["likes"])
