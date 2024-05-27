from django.urls import path

from apps.mypage import views

urlpatterns = [
    path("products/", views.MyProductListView.as_view(), name="my-products"),
    # path("interested-styles-products/", views.InterestedStyleProductListView.as_view(), name="interested-styles-products"),
    # path("interested-styles/", views.InterestedStyleUpdateView.as_view(), name="interested-styles"),
]
