from django import forms
from .models import *
from django.forms import inlineformset_factory

class ProductUploadForm(forms.Form):
    file = forms.FileField()


class UserCategoryForm(forms.ModelForm):
    class Meta:
        model = UserCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }




class UserCategoryMarkupForm(forms.ModelForm):
    class Meta:
        model = UserCategoryMarkup
        fields = ['product_type', 'markup_percentage']
        widgets = {
            'markup_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter markup percentage'
            }),
            'product_type': forms.HiddenInput(),  # Hide dropdown
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set product_type name for display in the template
        try:
            self.product_type_name = self.instance.product_type.name
        except Exception:
            product_type_id = self.initial.get('product_type')
            self.product_type_name = ""
            if product_type_id:
                try:
                    product_type_obj = ProductType.objects.get(id=product_type_id)
                    self.product_type_name = product_type_obj.name
                except ProductType.DoesNotExist:
                    pass

        # Optional: style delete checkbox
        if 'DELETE' in self.fields:
            self.fields['DELETE'].widget.attrs.update({'class': 'form-check-input'})




# # Count of ProductType records
# product_type_count = ProductType.objects.count()

# # Inline formset factory
# UserCategoryMarkupFormSet = inlineformset_factory(
#     UserCategory,
#     UserCategoryMarkup,
#     form=UserCategoryMarkupForm,
#     extra=product_type_count,  # One for each product type
#     can_delete=True
# )




class QueryForm(forms.ModelForm):
    class Meta:
        model = Query
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'Business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),            
        }

    
class CompositionForm(forms.ModelForm):
    class Meta:
        model = Composition
        fields = ['product_name', 'composition_name', 'product_type']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'composition_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_type': forms.TextInput(attrs={'class': 'form-control'}),
        }



class ProductTypeForm1(forms.ModelForm):
    class Meta:
        model = ProductType
        fields = ['name','markup_range']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product type name'}),
            'markup_range': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter default markup'}),
        }


class ProductMarkupByCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductMarkupByCategory
        fields = ['product', 'owner_margin', 'owner_selling_price', 'retailer_margin']
        widgets = {
            'owner_selling_price': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'retailer_margin': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        owner_margin = cleaned_data.get("owner_margin")

        if product and owner_margin is not None:
            buy_price = product.price or 0
            selling_price = buy_price + (buy_price * owner_margin / 100)
            cleaned_data["owner_selling_price"] = round(selling_price, 2)
            if product.MRP:
                cleaned_data["retailer_margin"] = round(product.MRP - selling_price, 2)
        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['created_by', 'updated_by', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'form': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product form'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'batch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch number'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'composition_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter composition name'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'MRP': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter MRP'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
        }