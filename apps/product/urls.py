from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.product.views import (
    ProductViewSet,
    RentalHistoryBorrowerView,
    RentalHistoryLenderView,
    RentalHistoryUpdateView,
)

router = DefaultRouter()
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    path("rental_history/borrow/", RentalHistoryBorrowerView.as_view(), name="borrowed_rental_history"),
    path("rental_history/lending/", RentalHistoryLenderView.as_view(), name="lending_rental_history"),
    path("rental_history/<int:pk>/", RentalHistoryUpdateView.as_view(), name="rental_history_update"),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
