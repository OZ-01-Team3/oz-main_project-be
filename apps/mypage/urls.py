from django.urls import path

from apps.mypage import views

urlpatterns = [
    path("products/", views.MyProductListView.as_view(), name="my-products"),
]
