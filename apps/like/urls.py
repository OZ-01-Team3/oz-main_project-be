from django.urls import path

from apps.like.views import LikeDestroyView, LikeListCreateView

urlpatterns = [
    path("", LikeListCreateView.as_view(), name="like_list"),
    # path("<uuid:pk>/", LikeCreateView.as_view(), name="like_create"),
    path("<uuid:pk>/", LikeDestroyView.as_view(), name="like_delete")
]
