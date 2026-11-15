from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timesince
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.PUBLISHED)
    
class Post(models.Model):
    # Добавляем константы для статуса
    DRAFT = 'draft'
    PUBLISHED = 'published'
    STATUS_CHOICES = [
        (DRAFT, 'Черновик'),
        (PUBLISHED, 'Опубликовано'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name="Автор")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posts', verbose_name="Категория"
    )
    # Новое поле статуса
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name="Статус"
    )
    # Новое поле для подсчета просмотров (будем увеличивать при каждом просмотре)
    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    objects = models.Manager()
    # Наш кастомный менеджер
    published = PublishedManager()

    def __str__(self):
        return self.title

    # Кастомный метод для получения абсолютной ссылки на пост
    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.id)])

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ['-created_at']
        # Добавляем индекс для ускорения поиска по статусу и дате
        indexes = [
            models.Index(fields=['-created_at', 'status']),
        ]

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',  # позволяет получить все комментарии поста через post.comments.all()
        verbose_name="Пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    def time_since_created(self):
        return timesince.timesince(self.created_at)
    def __str__(self):
        return f"Комментарий от {self.author.username} к {self.post.title}"
    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']  # сначала старые комментарии

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    def __str__(self):
        return f"Профиль пользователя {self.user.username}"
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"