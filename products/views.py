import pandas as pd
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, F

from UserManagement.models import *
from .forms import *
from .models import *
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from datetime import datetime
import re

# ----------------------------- Product Upload -----------------------------


def generate_next_product_id():
    last_product = Product.objects.filter(product_id__startswith='PRD').order_by('-product_id').first()
    if last_product and re.match(r'^PRD\d+$', last_product.product_id):
        last_number = int(last_product.product_id.replace('PRD', ''))
        new_number = last_number + 1
    else:
        new_number = 1
    return f'PRD{new_number:04d}'


# ----------------------------- Product Upload -----------------------------

#workingg code below 25-05-25

from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError


@login_required
def upload_products(request):
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']

            try:
                df = pd.read_excel(excel_file)
                df.columns = df.columns.str.strip()

                # Strip string columns to avoid trailing spaces
                for col in df.select_dtypes(include='object').columns:
                    df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

                # Required columns check
                required_columns = [
                    "Product", "Form", "Company", "Batch", "Expiry (MM/YY)", 
                    "MRP (Rs)", "Price-to_Retailer (Rs)",  "Units per Pack", "No of Packs", "Sale GST %"
                ]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    messages.error(request, f"Missing columns: {', '.join(missing_columns)}")
                    return render(request, 'productss/productss_upload.html', {'form': form})

                # Convert expiry date and validate
                df['Expiry (MM/YY)'] = pd.to_datetime(df['Expiry (MM/YY)'], format='%m/%y', errors='coerce')
                if df['Expiry (MM/YY)'].isnull().any():
                    messages.error(request, "One or more expiry dates are invalid. Please use MM/YY format.")
                    return render(request, 'productss/productss_upload.html', {'form': form})

                # Convert numeric columns safely
                df['No of Packs'] = pd.to_numeric(df['No of Packs'], errors='coerce').fillna(0).astype(int)
                df['Units per Pack'] = pd.to_numeric(df['Units per Pack'], errors='coerce').fillna(0).astype(int)
                df['GST %'] = pd.to_numeric(df['Sale GST %'], errors='coerce').fillna(0).astype(int)
                df['MRP (Rs)'] = pd.to_numeric(df['MRP (Rs)'], errors='coerce').fillna(0)
                df['Price-to_Retailer (Rs)'] = pd.to_numeric(df['Price-to_Retailer (Rs)'], errors='coerce').fillna(0)

                created_count = 0
                updated_count = 0

                with transaction.atomic():
                    for _, row in df.iterrows():
                        # Get composition for product if exists
                        composition = Composition.objects.filter(product_name=row['Product']).first()
                        composition_value = composition.composition_name if composition else None

                        if composition:
                            product_type_name = composition.product_type
                            product_type_obj = ProductType.objects.filter(name=product_type_name).first()
                            if not product_type_obj:
                                raise Exception(f"Product type '{product_type_name}' not found in ProductType table.")
                            product_type_id = product_type_obj.pk
                        else:
                            product_type_id = None

                        # Check if product exists
                        product = Product.objects.filter(
                            name=row['Product'],
                            MRP=row['MRP (Rs)'],
                            company=row['Company'],
                            expiry_date=row['Expiry (MM/YY)']
                        ).first()

                        if product:
                            # Update existing product quantity
                            product.quantity += row['No of Packs']
                            product.save()
                            updated_count += 1
                        else:
                            # Create new product
                            new_product_id = generate_next_product_id()
                            product = Product.objects.create(
                                product_id=new_product_id,
                                name=row['Product'],
                                form=row['Form'],
                                company=row['Company'],
                                batch=row['Batch'],
                                expiry_date=row['Expiry (MM/YY)'],
                                MRP=row['MRP (Rs)'],
                                price=row['Price-to_Retailer (Rs)'],
                                quantity=row['No of Packs'],
                                composition_name=composition_value,
                                pack_size=row['Units per Pack'],
                                GST=row['GST %'],
                                product_type_id=product_type_id,
                                created_by=request.user,
                                updated_by=request.user
                            )
                            created_count += 1

                            # Safety: ensure product saved properly before FK related creation
                            product.refresh_from_db()

                            # Calculate margins
                            owner_margin_percent = Decimal('15.00')
                            price = Decimal(row['Price-to_Retailer (Rs)'])
                            mrp = Decimal(row['MRP (Rs)'])

                            owner_margin_amount = (price * owner_margin_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            owner_selling_price = (price + owner_margin_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            retailer_margin = (mrp - owner_selling_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            retailer_margin_percent = ((retailer_margin / mrp) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if mrp else Decimal('0.00')

                            override_margin_block = owner_selling_price > mrp

                            # Create ProductPricingDetail
                            ProductPricingDetail.objects.create(
                                product=product,
                                owner_margin_percent=owner_margin_percent,
                                owner_margin_amount=owner_margin_amount,
                                owner_selling_price=owner_selling_price,
                                retailer_margin=retailer_margin,
                                retailer_margin_percent=retailer_margin_percent,
                                override_margin_block=override_margin_block
                            )

                            # Create UserCategoryProductMarkup entries for all user categories
                            user_categories = UserCategory.objects.all()
                            for user_category in user_categories:
                                UserCategoryProductMarkup.objects.get_or_create(
                                    user_category=user_category,
                                    product=product,
                                    defaults={
                                        'owner_margin_percent': owner_margin_percent,
                                        'owner_margin_amount': owner_margin_amount,
                                        'owner_selling_price': owner_selling_price,
                                        'retailer_margin': retailer_margin,
                                        'retailer_margin_percent': retailer_margin_percent,
                                        'override_margin_block': override_margin_block
                                    }
                                )

                messages.success(request, f"Upload successful! {created_count} products created, {updated_count} updated.")
                return redirect('upload')

            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")

        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = ProductUploadForm()

    return render(request, 'productss/productss_upload.html', {'form': form})

# views.py

@login_required

def user_category_margin_create_or_update(request, pk):
    user_category = get_object_or_404(UserCategory, pk=pk)
    products = Product.objects.all()

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith('owner_margin_percent_'):
                product_id = key.split('_')[-1]
                try:
                    product = Product.objects.get(id=product_id)
                    owner_margin_percent = Decimal(request.POST.get(f'owner_margin_percent_{product_id}', '0'))
                    discount = request.POST.get(f'discount_{product_id}', None)
                    scheme = request.POST.get(f'scheme_{product_id}', None)

                    price = product.price or Decimal('0')
                    mrp = product.MRP or Decimal('0')
                    owner_margin_amount = (price * owner_margin_percent / 100).quantize(Decimal('0.01'))
                    owner_selling_price = (price + owner_margin_amount).quantize(Decimal('0.01'))
                    retailer_margin = (mrp - owner_selling_price).quantize(Decimal('0.01'))
                    retailer_margin_percent = ((retailer_margin / mrp) * 100).quantize(Decimal('0.01')) if mrp else Decimal('0.00')

                    override_margin_block = owner_selling_price > mrp

                    markup, created = UserCategoryProductMarkup.objects.get_or_create(
                        user_category=user_category, product=product
                    )

                    # Always update values
                    markup.owner_margin_percent = owner_margin_percent
                    markup.owner_margin_amount = owner_margin_amount
                    markup.owner_selling_price = owner_selling_price
                    markup.retailer_margin = retailer_margin
                    markup.retailer_margin_percent = retailer_margin_percent
                    markup.discount_percent = discount or None
                    markup.scheme = scheme or None
                    markup.override_margin_block = override_margin_block
                    markup.save()

                except Product.DoesNotExist:
                    continue

        messages.success(request, "Markups updated successfully.")
        return redirect('user_category_markup_list')

    markup_map = {
        markup.product_id: markup for markup in UserCategoryProductMarkup.objects.filter(user_category=user_category)
    }

    # Attach markup to each product for easier access in template
    for product in products:
        product.markup = markup_map.get(product.id)

    return render(request, 'products/user_category_markup_update.html', {
        'user_category': user_category,
        'products': products
    })


# @login_required
# def upload_products(request):
#     if request.method == 'POST':
#         form = ProductUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             excel_file = request.FILES['file']

#             try:
#                 df = pd.read_excel(excel_file)
#                 df.columns = df.columns.str.strip()

#                 for col in df.select_dtypes(include='object').columns:
#                     df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

#                 required_columns = [
#                     "Product", "Form", "Company", "Batch", "Expiry (MM/YY)", 
#                     "MRP (Rs)", "Price-to_Retailer (Rs)",  "Units per Pack", "No of Packs", "GST %"
#                 ]
#                 missing_columns = [col for col in required_columns if col not in df.columns]

#                 if missing_columns:
#                     messages.error(request, f"Missing columns: {', '.join(missing_columns)}")
#                     return render(request, 'productss/productss_upload.html', {'form': form})

#                 df['Expiry (MM/YY)'] = pd.to_datetime(df['Expiry (MM/YY)'], format='%m/%y', errors='coerce')
#                 if df['Expiry (MM/YY)'].isnull().any():
#                     messages.error(request, "One or more expiry dates are invalid. Please use MM/YY format.")
#                     return render(request, 'productss/productss_upload.html', {'form': form})

#                 df['No of Packs'] = pd.to_numeric(df['No of Packs'], errors='coerce').fillna(0).astype(int)
#                 df['Units per Pack'] = pd.to_numeric(df['Units per Pack'], errors='coerce').fillna(0).astype(int)
#                 df['GST %'] = pd.to_numeric(df['GST %'], errors='coerce').fillna(0).astype(int)
#                 df['MRP (Rs)'] = pd.to_numeric(df['MRP (Rs)'], errors='coerce').fillna(0)
#                 df['Price-to_Retailer (Rs)'] = pd.to_numeric(df['Price-to_Retailer (Rs)'], errors='coerce').fillna(0)

#                 created_count = 0
#                 updated_count = 0

#                 with transaction.atomic():
#                     for _, row in df.iterrows():
#                         composition = Composition.objects.filter(product_name=row['Product']).first()
#                         composition_value = composition.composition_name if composition else None

#                         if composition:
#                             product_type_name = composition.product_type
#                             product_type_obj = ProductType.objects.filter(name=product_type_name).first()
#                             if not product_type_obj:
#                                 raise Exception(f"Product type '{product_type_name}' not found in ProductType table.")
#                             product_type_id = product_type_obj.pk
#                         else:
#                             product_type_id = None

#                         product = Product.objects.filter(
#                             name=row['Product'],
#                             MRP=row['MRP (Rs)'],
#                             company=row['Company'],
#                             expiry_date=row['Expiry (MM/YY)']
#                         ).first()

#                         if product:
#                             product.quantity += row['No of Packs']
#                             product.save()
#                             updated_count += 1
#                         else:
#                             new_product_id = generate_next_product_id()
#                             product = Product.objects.create(
#                                 product_id=new_product_id,
#                                 name=row['Product'],
#                                 form=row['Form'],
#                                 company=row['Company'],
#                                 batch=row['Batch'],
#                                 expiry_date=row['Expiry (MM/YY)'],
#                                 MRP=row['MRP (Rs)'],
#                                 price=row['Price-to_Retailer (Rs)'],
#                                 quantity=row['No of Packs'],
#                                 composition_name=composition_value,
#                                 pack_size=row['Units per Pack'],
#                                 GST=row['GST %'],
#                                 product_type_id=product_type_id,
#                                 created_by=request.user,
#                                 updated_by=request.user
#                             )
#                             created_count += 1

#                             # ---------------------
#                             # Calculate margin values
#                             # ---------------------
#                             owner_margin_percent = Decimal('15.00')
#                             price = Decimal(row['Price-to_Retailer (Rs)'])
#                             mrp = Decimal(row['MRP (Rs)'])

#                             owner_margin_amount = (price * owner_margin_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                             owner_selling_price = (price + owner_margin_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                             retailer_margin = (mrp - owner_selling_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                             retailer_margin_percent = ((retailer_margin / mrp) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if mrp else Decimal('0.00')

#                             override_margin_block = owner_selling_price > mrp

#                             ProductPricingDetail.objects.create(
#                                 product=product,
#                                 owner_margin_percent=owner_margin_percent,
#                                 owner_margin_amount=owner_margin_amount,
#                                 owner_selling_price=owner_selling_price,
#                                 retailer_margin=retailer_margin,
#                                 retailer_margin_percent=retailer_margin_percent,
#                                 override_margin_block=override_margin_block
#                             )
#                             # Create default UserCategory markups
#                             print("6666666666666666",owner_margin_percent,owner_margin_amount,owner_selling_price,retailer_margin,retailer_margin_percent,override_margin_block)

#                             user_categories = UserCategory.objects.all()
#                             print("9999999999999999",user_categories)
#                             for user_category in user_categories:
#                                 if not UserCategoryProductMarkup.objects.filter(user_category=user_category, product=product).exists():
#                                     UserCategoryProductMarkup.objects.create(
#                                         user_category=user_category,
#                                         product=product,
#                                         owner_margin_percent=owner_margin_percent,
#                                         owner_margin_amount=owner_margin_amount,
#                                         owner_selling_price=owner_selling_price,
#                                         retailer_margin=retailer_margin,
#                                         retailer_margin_percent=retailer_margin_percent,
#                                         override_margin_block=override_margin_block,
                                        
#                                     )


#                 messages.success(
#                     request, f"Upload successful! {created_count} products created, {updated_count} updated."
#                 )
#                 return redirect('upload')

#             except Exception as e:
#                 messages.error(request, f"Error processing file: {str(e)}")

#         else:
#             messages.error(request, "Invalid form submission.")

#     else:
#         form = ProductUploadForm()

#     return render(request, 'productss/productss_upload.html', {'form': form})



# ----------------------------- Product List & Filtering -----------------------------
# @login_required
# def product_list1(request):
#     """ List and filter products """
#     products = Product.objects.all()

#     # Filtering
#     name_query = request.GET.get('name', '').strip()
#     category_query = request.GET.get('category', '').strip()
#     price_min = request.GET.get('price_min')
#     price_max = request.GET.get('price_max')

#     if name_query:
#         products = products.filter(name__icontains=name_query)
#     if category_query:
#         products = products.filter(category__icontains=category_query)
#     if price_min:
#         products = products.filter(price__gte=price_min)
#     if price_max:
#         products = products.filter(price__lte=price_max)

#     return render(request, 'productss/productss_list.html', {'products': products})



@login_required
def product_order(request):
    """ List and filter products for ordering """
    products = Product.objects.all()

    # Filtering
    name_query = request.GET.get('name', '').strip()
    Company_query = request.GET.get('company', '').strip()
    print(Company_query)
    if name_query:
        products = products.filter(name__icontains=name_query)

    if Company_query:
        products = products.filter(company__icontains=Company_query)

    return render(request, 'productss/productss_orders.html', {'products': products})

# ----------------------------- Order Management -----------------------------
@login_required
def place_order(request):
    """ Handle order placement via AJAX """
    if request.method == "POST":
        try:

            cart_data = json.loads(request.body)
            total_quantity = sum(item["quantity"] for item in cart_data)
            total_price = sum(item["total"] for item in cart_data)

            order = Order.objects.create(total_quantity=total_quantity, total_price=total_price,created_by=request.user)

            order_items = []
            for item in cart_data:
                product = get_object_or_404(Product, pk=item["id"])
                if product.quantity >= item["quantity"]:
                    product.quantity = F('quantity') - item["quantity"]  # Reduce stock safely
                    product.save(update_fields=['quantity'])

                    order_items.append(
                        OrderItem(
                            order=order,
                            product=product,
                            quantity=item["quantity"],
                            total_price=item["total"],
                            created_by=request.user
                        )
                    )
                    user = get_object_or_404(User, id=request.user.id)
                
                else:
                    return JsonResponse({"error": f"Not enough stock for {product.name}"}, status=400)
            total_amount = total_price   # Assuming `cart_items` is available
            print('aaa',total_amount)
            point_allocation = PointAllocation.objects.filter(
                Q(min_amount__lte=total_amount) & 
                (Q(max_amount__gte=total_amount) | Q(max_amount__isnull=True))
            ).first()
            print('ppp',point_allocation)
            # Assign points if a range is found
            points = point_allocation.points if point_allocation else 0
            user.points+=points
            user.save()
            OrderItem.objects.bulk_create(order_items)  # Bulk insert order items
            return JsonResponse({"message": "Order placed successfully", "order_id": order.id})

        except Exception as e:
            return JsonResponse({"error": f"Error placing order: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

def order_list(request):
    """ List all orders with related items """
    orders = Order.objects.prefetch_related("items__product").all()
    return render(request, "productss/orders_list.html", {"orders": orders})


def recent_order_list(request):
    """List the last 5 orders with related items"""
    orders = Order.objects.prefetch_related("items__product").order_by("-created_at")[:5]
    return render(request, "productss/orders_list.html", {"orders": orders})

def delivered_list(request):
    """ List all orders with related items """
    orders = Order.objects.prefetch_related("items__product").filter(status='delivered')
    return render(request, "productss/orders_list.html", {"orders": orders})


def order_update(request,pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.updated_by = request.user
                order.save()
                messages.success(request, "order updated successfully!")
                return redirect('order_list')
            except Exception as e:
                messages.error(request, f"Error updating order: {e}")
    else:
        form = OrderForm(instance=order)
    return render(request, 'productss/order_form.html', {'form': form})




@login_required
def query_list(request):
    try:
        queries = Query.objects.all()
        return render(request, 'productss/query_list.html', {'queries': queries})
    except Exception as e:
        messages.error(request, f"Error fetching queries: {e}")
        return render(request, 'productss/query_list.html', {'queries': []})  

@login_required
def query_create(request):
    if request.method == 'POST':
        form = QueryForm(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            try:
                query = form.save(commit=False)
                query.created_by = request.user
                query.updated_by = request.user
                query.save()
                messages.success(request, "Query submitted successfully!")
                return redirect('query_list')
            except Exception as e:
                messages.error(request, f"Error submitting query: {e}")
    else:
        form = QueryForm()
    return render(request, 'productss/query_form.html', {'form': form})

@login_required
def query_update(request, pk):
    query = get_object_or_404(Query, pk=pk)
    if request.method == 'POST':
        form = QueryForm(request.POST, request.FILES, instance=query)
        if form.is_valid():
            try:
                query = form.save(commit=False)
                query.updated_by = request.user
                query.save()
                messages.success(request, "Query updated successfully!")
                return redirect('query_list')
            except Exception as e:
                messages.error(request, f"Error updating query: {e}")
    else:
        form = QueryForm(instance=query)
    return render(request, 'productss/query_form.html', {'form': form})

@login_required
def query_delete(request, pk):
    try:
        query = get_object_or_404(Query, pk=pk)
        query.delete()
        messages.success(request, "Query deleted successfully!")
        return redirect('query_list')
    except Exception as e:
        messages.error(request, f"Error deleting query: {e}")







def extract_columns(request):
    file_url = None  # Initialize file_url to None
    error_message = None  # Initialize error_message to None

    if request.method == "POST" and request.FILES.get("excel_file"):
        try:
            uploaded_file = request.FILES["excel_file"]
            fs = FileSystemStorage()
            file_path = fs.save(uploaded_file.name, uploaded_file)

            # Read Excel file and skip the first 12 rows
            df = pd.read_excel(fs.path(file_path), skiprows=12)

            # Select specific columns
            selected_columns = [
                "Product", "Form", "Company", "Batch", "Expiry (MM/YY)", 
                "MRP (Rs)", "Price-to_Retailer (Rs)", "Units per Pack","No of Packs","Sale GST %"
            ]

            # Ensure only existing columns are selected
            available_columns = [col for col in selected_columns if col in df.columns]
            if not available_columns:
                raise ValueError("None of the required columns exist in the uploaded file.")

            df_selected = df[available_columns]
            time = datetime.now().strftime("%Y%m%d_%H%M")
            output_filename = f"productDetail_{time}.xlsx"
            output_path = fs.path(output_filename)
            df_selected.to_excel(output_path, index=False)

            # Generate file URL for downloading
            file_url = fs.url(output_filename)

        except Exception as e:
            error_message = f"Error: {str(e)}"

    return render(request, "productss/upload.html", {"file_url": file_url, "error_message": error_message})

def delete_all_products(request):
    """ Delete all products from the database """
    try:
        deleted_count, _ = Product.objects.all().delete()
        messages.success(request, f"Successfully deleted {deleted_count} products.")
    except Exception as e:
        messages.error(request, f"Error deleting products: {str(e)}")

    return redirect('product_list')  # Redirect to product list page


# def calculate_margins(price: Decimal, mrp: Decimal, margin_percent: Decimal):
#     """
#     Calculate margin amount, owner selling price, and retailer margin.
#     Returns: (margin_amount, owner_selling_price, retailer_margin, margin_exceeds)
#     """
#     try:
#         price = Decimal(price)
#         mrp = Decimal(mrp)
#         margin_percent = Decimal(margin_percent)

#         margin_amount = (price * margin_percent) / Decimal(100)
#         owner_selling_price = price + margin_amount
#         retailer_margin = mrp - owner_selling_price
#         margin_exceeds = owner_selling_price > mrp

#         return margin_amount, owner_selling_price, retailer_margin, margin_exceeds

#     except Exception:
#         return Decimal(0), Decimal(0), Decimal(0), False


# def update_all_products(request):
#     """ Upload or update products from an Excel file and overwrite the quantity """
#     if request.method == 'POST':
#         form = ProductUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             excel_file = request.FILES['file']
#             try:
#                 df = pd.read_excel(excel_file)

#                 # Ensure required columns exist
#                 required_columns = [
#                     "Product", "Form", "Company", "Batch", "Expiry (MM/YY)",
#                     "MRP (Rs)", "Price-to_Retailer (Rs)", "Stock Age"
#                 ]
#                 missing_columns = [col for col in required_columns if col not in df.columns]
#                 if missing_columns:
#                     messages.error(request, f"Missing columns: {', '.join(missing_columns)}")
#                     return render(request, 'productss/productss_upload.html', {'form': form})

#                 # Normalize Expiry Date
#                 df['Expiry (MM/YY)'] = pd.to_datetime(df['Expiry (MM/YY)'], format='%m/%y', errors='coerce')
#                 df['Expiry (MM/YY)'] = df['Expiry (MM/YY)'].dt.strftime('%Y-%m-01')

#                 # Convert numeric fields
#                 df['Stock Age'] = pd.to_numeric(df['Stock Age'], errors='coerce').fillna(0).astype(int)
#                 df['MRP (Rs)'] = pd.to_numeric(df['MRP (Rs)'], errors='coerce').fillna(0)
#                 df['Price-to_Retailer (Rs)'] = pd.to_numeric(df['Price-to_Retailer (Rs)'], errors='coerce').fillna(0)

#                 # Begin atomic transaction
#                 with transaction.atomic():
#                     default_margin = Decimal(15.00)

#                     for _, row in df.iterrows():
#                         name = row['Product']
#                         form = row['Form']
#                         company = row['Company']
#                         batch = row['Batch']
#                         expiry = row['Expiry (MM/YY)']
#                         mrp = Decimal(row['MRP (Rs)'])
#                         price = Decimal(row['Price-to_Retailer (Rs)'])
#                         quantity = int(row['Stock Age'])

#                         # Calculate margins
#                         _, owner_price, retailer_margin, exceeds = calculate_margins(
#                             price=price,
#                             mrp=mrp,
#                             margin_percent=default_margin
#                         )

#                         # Create or update product
#                         Product.objects.update_or_create(
#                             name=name,
#                             MRP=mrp,
#                             company=company,
#                             expiry_date=expiry,
#                             defaults={
#                                 'form': form,
#                                 'batch': batch,
#                                 'price': price,
#                                 'quantity': quantity,
#                                 'margin': default_margin,
#                                 'owner_selling_price': owner_price,
#                                 'retailer_margin': retailer_margin,
#                                 'margin_exceeds_mrp': exceeds,
#                                 'updated_by': request.user,
#                             }
#                         )

#                 messages.success(request, "Products updated successfully!")
#                 return redirect('upload')

#             except Exception as e:
#                 messages.error(request, f"Error processing file: {str(e)}")
#     else:
#         form = ProductUploadForm()

#     return render(request, 'productss/productss_upload.html', {'form': form})




def update_all_products(request):
    """ Upload or update products from an Excel file and overwrite the quantity """
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)

                # Ensure required columns exist
                required_columns = ["Product", "Form", "Company", "Batch", "Expiry (MM/YY)", 
                                    "MRP (Rs)", "Price-to_Retailer (Rs)", "Stock Age"]
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    messages.error(request, f"Missing columns: {', '.join(missing_columns)}")
                    return render(request, 'productss/productss_upload.html', {'form': form})

                # Convert Expiry Date safely
                df['Expiry (MM/YY)'] = pd.to_datetime(df['Expiry (MM/YY)'], format='%m/%y', errors='coerce')
                df['Expiry (MM/YY)'] = df['Expiry (MM/YY)'].dt.strftime('%Y-%m-01')  # Normalize to first of month

                # Convert Stock Age to Integer
                df['Stock Age'] = pd.to_numeric(df['Stock Age'], errors='coerce').fillna(0).astype(int)

                # Ensure Price Columns are Numeric
                df['MRP (Rs)'] = pd.to_numeric(df['MRP (Rs)'], errors='coerce').fillna(0)
                df['Price-to_Retailer (Rs)'] = pd.to_numeric(df['Price-to_Retailer (Rs)'], errors='coerce').fillna(0)

                # Begin transaction to ensure atomic operations
                with transaction.atomic():
                    for _, row in df.iterrows():
                        # Check for existing product based on Name, MRP, Company, and Expiry Date
                        product, created = Product.objects.update_or_create(
                            name=row['Product'],
                            MRP=row['MRP (Rs)'],
                            company=row['Company'],
                            expiry_date=row['Expiry (MM/YY)'],
                            defaults={
                                'form': row['Form'],
                                'batch': row['Batch'],
                                'price': row['Price-to_Retailer (Rs)'],
                                'quantity': row['Stock Age'],  # Overwrites quantity
                                'updated_by': request.user
                            }
                        )

                messages.success(request, "Products updated successfully!")
                return redirect('upload')

            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")

    else:
        form = ProductUploadForm()

    return render(request, 'productss/productss_upload.html', {'form': form})


from django.http import HttpResponse

# List Compositions

@login_required  # Remove this if login is not required
def composition_list(request):
    try:
        compositions = Composition.objects.all()
        return render(request, 'products/composition_list.html', {'compositions': compositions})
    except Exception as e:
        messages.error(request, f"Error creating composition: {e}") 

# Create Composition

def composition_create(request):
    form = CompositionForm(request.POST or None)
    if form.is_valid():
        try:
            composition = form.save(commit=False)
            composition.created_by = request.user
            composition.save()
            messages.success(request, "Composition added successfully!")
            return redirect('composition_list')
        except Exception as e:
            messages.error(request, f"Error creating composition: {e}")
    return render(request, 'products/composition_form.html', {'form': form})

# Update Composition
@login_required
def composition_update(request, pk):
    composition = get_object_or_404(Composition, pk=pk)
    form = CompositionForm(request.POST or None, instance=composition)
    if form.is_valid():
        try:
            composition = form.save(commit=False)
            composition.updated_by = request.user
            composition.save()
            messages.success(request, "Composition updated successfully!")
            return redirect('composition_list')
        except Exception as e:
            messages.error(request, f"Error updating composition: {e}")
    return render(request, 'products/composition_form.html', {'form': form})

# Delete Composition
@login_required
def composition_delete(request, pk):
    try:
        composition = get_object_or_404(Composition, pk=pk)
        composition.delete()
        messages.success(request, "Composition deleted successfully!")
        return redirect('composition_list')
    except Exception as e:
        messages.error(request, f"Error deleting composition: {e}")





from django.http import JsonResponse
import pandas as pd
from django.db import transaction
from django.shortcuts import redirect
from .models import Composition, ProductType

from django.http import JsonResponse
import pandas as pd
from django.db import transaction
from django.shortcuts import redirect
from .models import Composition, ProductType

def upload_composition_from_excel(request):
    if request.method == "POST" and request.FILES.get("excel_file"):
        try:
            uploaded_file = request.FILES["excel_file"]
           
             # Validate Excel File
            try:
                df = pd.read_excel(uploaded_file)
            except Exception as e:
                return JsonResponse({"error": f"Invalid Excel file: {str(e)}"}, status=400)
             # Check for Required Columns
            required_columns = {"Product", "Composition", "Product Type"}
            if not required_columns.issubset(df.columns):
                return JsonResponse({"error": "Missing required columns in Excel file"}, status=400)

            compositions = []
            existing_compositions = set(
                Composition.objects.values_list("product_name", "composition_name", "product_type")
            )

#             # Fetch existing ProductTypes to avoid duplicate creation
            product_types = {pt.name: pt for pt in ProductType.objects.all()}

            for _, row in df.iterrows():
                product_name = str(row.get("Product", "")).strip()
                composition_name = str(row.get("Composition", "")).strip()
                product_type_name = str(row.get("Product Type", "")).strip()

                # Skip rows with missing product or composition
                if not product_name or not composition_name:
                    continue  

#                 # Create ProductType if it doesn't exist
                if product_type_name and product_type_name not in product_types:
                    product_type, _ = ProductType.objects.get_or_create(name=product_type_name)
                    product_types[product_type_name] = product_type  # Update dictionary
                else:
                    product_type = product_types.get(product_type_name)

#                 # Ensure product_type_name is stored as a string (None converted to "")
                product_type_name = product_type.name if product_type else ""

#                 # Check if composition already exists
                if (product_name, composition_name, product_type_name) in existing_compositions:
                    continue  # Skip duplicate composition

#                 # Append new composition
                compositions.append(
                    Composition(
                        product_name=product_name,
                        composition_name=composition_name,
                        product_type=product_type_name
                    )
                )
                
#                 # Add to existing_compositions to prevent duplicates in the same file
                existing_compositions.add((product_name, composition_name, product_type_name))

#             # Bulk Insert New Compositions
            with transaction.atomic():
                Composition.objects.bulk_create(compositions)

            return redirect('composition_list')

        except Exception as e:
            return JsonResponse({"error": f"Processing error: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request or file not provided"}, status=400)

def upload_compositions(request):
    return render(request, 'products/upload_composition.html')


def delll(request):
    a=Composition.objects.all().delete()
    b=ProductType.objects.all().delete()
    return HttpResponse("Deleted all compositions and product types")

def delll11(request):
    a=Product.objects.all().delete()
    return HttpResponse("Deleted all compositions and product types")

# @login_required
def product_list(request):
    try:
        products = Product.objects.all()
        return render(request, 'products/product_list.html', {'products': products})
    except Exception as e:
        messages.error(request, f"Error fetching products: {e}")
        return render(request, 'products/product_list.html', {'products': []}) 

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.created_by = request.user  
                product.save()
                messages.success(request, "Product added successfully!")
                return redirect('product_list')
            except Exception as e:
                messages.error(request, f"Error creating product: {e}")
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.updated_by = request.user  
                product.save()
                messages.success(request, "Product updated successfully!")
                return redirect('product_list')
            except Exception as e:
                messages.error(request, f"Error updating product: {e}")
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_delete(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('product_list')
    except Exception as e:
        messages.error(request, f"Error deleting product: {e}")



@login_required
def product_type_list(request):
    try:
        product_types = ProductType.objects.all()
        return render(request, 'products/product_type_list.html', {'product_types': product_types})
    except Exception as e:
        messages.error(request, f"Error fetching product types: {e}")

@login_required
def product_type_create(request):
    if request.method == 'POST':
        form = ProductTypeForm1(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Product Type added successfully!")
                return redirect('product_type_list')
            except Exception as e:
                messages.error(request, f"Error creating product type: {e}")
    else:
        form = ProductTypeForm1()
    return render(request, 'products/product_type_form.html', {'form': form})

@login_required
def product_type_update(request, pk):
    product_type = get_object_or_404(ProductType, pk=pk)
    if request.method == 'POST':
        form = ProductTypeForm1(request.POST, instance=product_type)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Product Type updated successfully!")
                return redirect('product_type_list')
            except Exception as e:
                messages.error(request, f"Error updating product type: {e}")
    else:
        form = ProductTypeForm1(instance=product_type)
    return render(request, 'products/product_type_form.html', {'form': form})

@login_required
def product_type_delete(request, pk):
    try:
        product_type = get_object_or_404(ProductType, pk=pk)
        product_type.delete()
        messages.success(request, "Product Type deleted successfully!")
        return redirect('product_type_list')
        
    except Exception as e:
        messages.error(request, f"Error deleting product type: {e}")



# @login_required
# def product_list(request):
#     user = request.user  # Get the logged-in user
#     products = Product.objects.all()  # Fetch all products
    
#     # Fetch all user-specific markups
#     user_markups = UserProductMarkup.objects.filter(user=user)
#     markup_dict = {markup.product_type.id: markup.markup_percentage for markup in user_markups}

#     for product in products:
#         product.user_price = product.get_customer_price(user)  # Calculate price based on markup
    
#     return render(request, "products/product_list.html", {"products": products})


@login_required
def user_product_list(request):
    user = request.user  # Get the logged-in user

    products = Product.objects.all()  # Fetch all product
    for product in products:
        product.user_price = product.get_customer_price(user) 
    return render(request, "products/user_product_list.html", {"products": products})


from django.shortcuts import get_object_or_404
from .models import Product, UserCategoryMarkup, UserCategory

@login_required
def product_markups(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_categories = UserCategory.objects.all()

    category_prices = []
    for category in user_categories:
        markup = UserCategoryMarkup.objects.filter(
            category=category, product_type=product.product_type
        ).first()
        markup_percentage = markup.markup_percentage if markup else 0

        final_price = product.price * (Decimal('1') + Decimal(markup_percentage) / Decimal('100'))
        category_prices.append({
            'category': category,
            'markup': markup_percentage,
            'final_price': round(final_price, 2)
        })

    return render(request, "products/product_markups.html", {
        "product": product,
        "category_prices": category_prices
    })



@login_required
def user_category_list(request):
    categories = UserCategory.objects.all()
    return render(request, 'products/user_category_list.html', {'categories': categories})

@login_required
def user_category_create(request):
    if request.method == 'POST':
        form = UserCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.updated_by = request.user
            category.save()
            messages.success(request, "Category created successfully!")
            return redirect('user_category_list')
    else:
        form = UserCategoryForm()
    return render(request, 'products/user_category_form.html', {'form': form})

@login_required
def user_category_update(request, pk):
    category = get_object_or_404(UserCategory, pk=pk)
    if request.method == 'POST':
        form = UserCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.updated_by = request.user
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('user_category_list')
    else:
        form = UserCategoryForm(instance=category)
    return render(request, 'products/user_category_form.html', {'form': form})

@login_required
def user_category_delete(request, pk):
    category = get_object_or_404(UserCategory, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return redirect('user_category_list')



@login_required
def user_category_markup_create_or_update(request, category_id):
    category = get_object_or_404(UserCategory, id=category_id)
    products = Product.objects.all()

    # Create or get existing markup objects
    for product in products:
        UserCategoryProductMarkup.objects.get_or_create(
            category=category,
            product=product,
            defaults={'owner_margin': 0}
        )

    MarkupFormSet = modelformset_factory(
        UserCategoryProductMarkup,
        form=UserCategoryProductMarkupForm,
        extra=0,
        can_delete=False
    )

    queryset = UserCategoryProductMarkup.objects.filter(category=category).select_related('product')

    if request.method == 'POST':
        formset = MarkupFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    markup = form.save(commit=False)
                    product = markup.product

                    buy_price = product.price or 0
                    mrp = product.MRP or 0
                    owner_margin = markup.owner_margin or 0

                    # Auto-calculated fields
                    owner_selling_price = buy_price + (buy_price * owner_margin / 100)
                    retailer_margin = mrp - owner_selling_price

                    markup.owner_selling_price = owner_selling_price
                    markup.retailer_margin = retailer_margin
                    markup.category = category
                    markup.updated_by = request.user
                    if not markup.pk:
                        markup.created_by = request.user
                    markup.save()
            messages.success(request, "Product markup successfully updated.")
            return redirect('user_category_markup_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        formset = MarkupFormSet(queryset=queryset)

    return render(request, 'markup_form_product_level.html', {
        'formset': formset,
        'category': category,
    })



@login_required
def user_category_markup_list(request):
    categories = UserCategory.objects.all()
    return render(request, 'products/user_category_markup_list.html', {'categories': categories})



@login_required
def user_category_markup_detail(request, category_id):
    category = get_object_or_404(UserCategory, id=category_id)
    markups = UserCategoryMarkup.objects.filter(category=category)
    return render(request, 'products/user_category_markup_detail.html', {'category': category, 'markups': markups})



@login_required
def user_category_markup_edit(request, pk):
    markup = get_object_or_404(UserCategoryMarkup, pk=pk)
    
    if request.method == 'POST':
        form = UserCategoryMarkupForm(request.POST, instance=markup)
        if form.is_valid():
            edited_markup = form.save(commit=False)
            edited_markup.updated_by = request.user
            edited_markup.save()
            messages.success(request, "Markup updated successfully.")
            return redirect('user_category_markup_list')

    else:
        form = UserCategoryMarkupForm(instance=markup)
    
    return render(request, 'products/user_category_markup_edit.html', {'form': form, 'title': 'Edit Markup'})



@login_required
def user_category_markup_delete(request, pk):
    markup = get_object_or_404(UserCategoryMarkup, pk=pk)
    category_id = markup.category.id
    try:
        markup.delete()
        messages.success(request, "Markup deleted successfully.")
        return redirect('user_category_markup_list')
    except Exception as e:
        messages.error(request, f"Error deleting markup: {e}")


    products = Product.objects.all()  # Fetch all products
    
    # Fetch user-specific markups
    user_markups = UserProductMarkup.objects.filter(user=user)
    markup_dict = {markup.product_type.id: markup.markup_percentage for markup in user_markups}

    for product in products:
        # Fetch composition for the specific product
        composition = Composition.objects.filter(product_name=product.name).first()
        if composition:
            product.composition_name = composition.composition_name  # Assign composition name
            
            # Fetch the correct ProductType instance
            product_type_instance = ProductType.objects.filter(name=composition.product_type).first()
            if product_type_instance:
                product.product_type = product_type_instance  # Assign the actual ProductType instance

        # Ensure `user_price` is assigned correctly
            product.user_price = product.get_customer_price(user)

    return render(request, "user/product_list.html", {"products": products})


@login_required
def admin_product_list(request):
    products = Product.objects.all() 

    return render(request, "products/product_list.html", {"products": products})


