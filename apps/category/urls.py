from django.urls import path

from apps.category.views import CategoryListView

urlpatterns = [
    path("", CategoryListView.as_view(), name="category-list"),
]
