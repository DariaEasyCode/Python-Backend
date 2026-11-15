from django.contrib import admin
from .models import Category, Post, Comment, Profile
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'category', 'status', 'views_count', 'created_at')
    list_filter = ('status', 'category', 'author', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    # Добавляем возможность редактировать статус прямо в списке
    list_editable = ('status',)
    # Поля, которые только для чтения (просмотры не должны редактироваться вручную)
    readonly_fields = ('views_count',)
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('text',)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'birth_date')
    search_fields = ('user__username', 'bio')  # Поиск по полю связанной модели