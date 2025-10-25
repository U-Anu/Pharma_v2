from django import forms
from .models import *
from django import forms
from .models import NewsArticle

class NewsArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticle
        exclude = ['created_at', 'updated_at', 'published_at','created_by','updated_by']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter news title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter content...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
