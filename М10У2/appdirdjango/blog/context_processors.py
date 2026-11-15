from .models import Category

def categories(request):
    """Добавляет список всех категорий в контекст шаблонов"""
    return {
        'categories': Category.objects.all()
    }