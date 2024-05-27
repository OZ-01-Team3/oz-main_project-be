from django.urls import path

from apps.category.views import CategoryListView, StyleListView

urlpatterns = [
    path("", CategoryListView.as_view(), name="category-list"),
    path("styles/", StyleListView.as_view(), name="style-list"),
]
