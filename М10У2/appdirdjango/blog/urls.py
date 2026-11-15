# blog/urls.py
from django.urls import path
from . import views
from .views import (
    home, PostListView, CategoryPostListView, PostDetailView,
    PostCreateView, PostUpdateView, PostDeleteView
)

urlpatterns = [
    path('', home, name='home'),
    path('posts/', PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post/new/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('category/<int:category_id>/', CategoryPostListView.as_view(), name='category_posts'),
]