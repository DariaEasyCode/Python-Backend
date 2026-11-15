from django.urls import path
from . import views
from .views import PostListView, CategoryPostListView, PostDetailView

urlpatterns = [
    path('', views.home, name='home'),
    path('posts/', PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('category/<int:category_id>/', CategoryPostListView.as_view(), name='category_posts'),
]
