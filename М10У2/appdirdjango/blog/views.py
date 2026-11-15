from django.shortcuts import render, get_object_or_404
from .models import Category, Post
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import PostForm
def home(request):
    # Используем наш новый менеджер published, чтобы показывать только опубликованные посты
    posts = Post.published.all()[:5]
    return render(request, 'blog/home.html', {'posts': posts})

# Новое представление для детальной страницы поста
def post_detail(request, post_id):
    # get_object_or_404 либо вернет пост, либо вызовет ошибку 404
    post = get_object_or_404(Post, id=post_id, status=Post.PUBLISHED)
    
    # Увеличиваем счетчик просмотров
    post.views_count += 1
    post.save(update_fields=['views_count'])  # update_fields для оптимизации
    
    # Получаем все комментарии к этому посту
    comments = post.comments.all()
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
    })

from django.views.generic import ListView, DetailView
from .models import Post

class PostListView(ListView):
    """Список всех опубликованных постов с пагинацией"""
    model = Post
    template_name = 'blog/post_list.html'   # явно указываем шаблон
    context_object_name = 'posts'           # имя переменной в шаблоне
    paginate_by = 5                          # количество постов на странице

    def get_queryset(self):
        """Выбираем только опубликованные посты, сортируем по дате"""
        return Post.published.all().select_related('author', 'category')
    
class CategoryPostListView(ListView):
    """Список постов в указанной категории"""
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 5
    def get_queryset(self):
        # Получаем идентификатор категории из URL
        category_id = self.kwargs['category_id']
        # Фильтруем посты по категории и статусу опубликовано
        return Post.published.filter(category_id=category_id).select_related('author', 'category')
    def get_context_data(self, **kwargs):
        # Добавляем в контекст название категории для отображения в шаблоне
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs['category_id']
        category = Category.objects.get(id=category_id)
        context['category'] = category
        return context
    
class PostDetailView(DetailView):
    """Детальная страница поста"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        # Показываем только опубликованные посты
        return Post.published.all().select_related('author', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем комментарии к посту
        context['comments'] = self.object.comments.all().select_related('author')
        # Увеличиваем счётчик просмотров
        post = self.object
        post.views_count += 1
        post.save(update_fields=['views_count'])
        return context
    
class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста"""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')  # после создания перенаправляем на список постов

    def form_valid(self, form):
        # Устанавливаем автором текущего пользователя
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста"""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        # Проверяем, что текущий пользователь - автор поста или суперпользователь
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_superuser
    
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление поста"""
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_superuser
    