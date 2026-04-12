from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthenticationForm(forms.Form):
    email=forms.CharField(max_length=50,required=True,widget=forms.TextInput(attrs={'placeholder': 'Enter your Email ID'}))
    password = forms.CharField( widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}), required=True)



class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Link to your custom User model
        fields = ('shop_name','drug_license','GST_number','license_expiry_date','address', 'phone_number','alternate_phone_number',  'profile_image', 'drug_license_image', 'email', )
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter shop name'}),
            'drug_license': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter drug license number'}),
            'GST_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter GST number'}),
            'license_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Select license expiry date', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your address', 'rows': 3}),
            'phone_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'alternate_phone_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your alternate_phone_number'}),
            # 'dob': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Select your date of birth', 'type': 'date'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'drug_license_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
            # 'gender': forms.Select(attrs={'class': 'form-control'}),
           'password1' : forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password1'
        }),
        label='Password'
    ),
    'password2' : forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'password2'
        }),
        label='Confirm Password'
    )
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        
        return password2
    

class PointAllocationForm(forms.ModelForm):
    class Meta:
        model = PointAllocation
        exclude = []
        widgets = {
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum amount'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter maximum amount (optional)'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter points'}),
        }