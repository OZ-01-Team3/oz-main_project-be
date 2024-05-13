from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.product.views import ProductViewSet

router = DefaultRouter()
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
