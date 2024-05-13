from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.product.views import ProductViewSet

router = DefaultRouter()
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

# from django.urls import path
#
# from apps.product.views import (  # ProductStatusUpdateAPIView
#     ProductCreateAPIView,
#     ProductDeleteAPIView,
#     ProductDetailAPIView,
#     ProductListAPIView,
#     ProductPartialUpdateAPIView,
#     ProductSearchAPIView,
#     ProductUpdateAPIView,
# )
#
# urlpatterns = [
#     path("", ProductListAPIView.as_view(), name="product-list"),
#     path("", ProductCreateAPIView.as_view(), name="product-create"),
#     path("<int:product_id>/", ProductDetailAPIView.as_view(), name="product-detail"),
#     path("<int:product_id>/", ProductUpdateAPIView.as_view(), name="product-update"),
#     path("<int:product_id>/",ProductPartialUpdateAPIView.as_view(),name="product-partial-update",),
#     path("<int:product_id>/", ProductDeleteAPIView.as_view(), name="product-delete"),
#     path("", ProductSearchAPIView.as_view(), name="product-search"),
#     # path("api/products/, ProductStatusUpdateAPIView.as_view(), name='product-status-update'),
# ]
