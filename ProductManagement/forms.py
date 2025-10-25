from django import forms
from .models import *

from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'composition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter composition'}),
            'brands': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter brand name'}),
            'schedule': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'pack_size': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch number'}),
            'requires_prescription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
