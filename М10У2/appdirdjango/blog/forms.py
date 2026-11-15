# blog/forms.py
from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'status']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'category': 'Категория',
            'status': 'Статус',
        }