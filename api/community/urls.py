from django.urls import path

from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view()),
    path('posts/<int:post_id>/like/', views.PostLikeView.as_view()),
]
