from django import forms
from .models import *

class StatusForm(forms.ModelForm):
    class Meta:
        model = UserMemo
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
             'user': forms.Select(attrs={'class': 'form-control'}), 
            'description': forms.TextInput(attrs={'class': 'form-control','rows': 3, 'placeholder': 'Enter description'}),
        }

class CertificationStatusForm(forms.ModelForm):
    class Meta:
        model = CertificationStatus
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Certification name e.g(Active,Expired)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country code'}),
        }

class StateForm(forms.ModelForm):
    class Meta:
        model = State
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state name'}),
            'country': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for selecting country
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city name'}),
            'state': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for selecting state
        }

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter certification name'}),
            'issued_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter issuing authority'}),
            'certification_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter certification number'}),
            'status': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for status selection
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter any notes'}),
            'certification_document': forms.FileInput(attrs={'class': 'form-control'}),  # File upload input
        }
class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter description '}),
        }
class ScheduleTypesForm(forms.ModelForm):
    class Meta:
        model = ScheduleTypes
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'schedule_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter schedule code'}),
            'schedule_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter schedule name '}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter description '}),

        }
class NewsCategoryForm(forms.ModelForm):
    class Meta:
        model = NewsCategory
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter description '}),
        }