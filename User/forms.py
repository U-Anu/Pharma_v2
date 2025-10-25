from products.models import OrderItem
from django import forms
from .models import *
from django.forms import modelformset_factory
from .models import *
from django.forms import inlineformset_factory

class OrderForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control', 'rows': 4}),
        }


class CustomerOrderForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = ['customer_name', 'number']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'rows': 4}),
            'number': forms.NumberInput(attrs={'class': 'form-control', 'rows': 4}),
        }
        
class OrderItemTempForm(forms.ModelForm):
    class Meta:
        model = OrderItemTemp
        fields = ['product_name', 'product_type', 'quantity', 'notes']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'product_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
