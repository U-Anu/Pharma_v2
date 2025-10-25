from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from Master.models import ProductCategory
from .models import Product
from .forms import ProductForm

# ----------------------------- Product CRUD -----------------------------

def product_list(request):
    """ List and search products """
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")

    products = Product.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(composition__icontains=query))

    if category_id:
        products = products.filter(category_id=category_id)

    categories = ProductCategory.objects.all()  # Fetch categories for filtering
    return render(request, "products/product_list.html", {"products": products, "categories": categories})

@login_required
def product_create(request):
    """ Create a new product """
    form = ProductForm(request.POST or None)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_update(request, pk):
    """ Update an existing product """
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f"Error updating product: {e}")
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_delete(request, pk):
    """ Delete a product """
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
            messages.success(request, "Product deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting product: {e}")
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
