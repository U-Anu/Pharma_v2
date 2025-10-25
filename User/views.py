from django.shortcuts import render
from django.urls import reverse
from products.forms import QueryForm
from products.models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from UserManagement.models import *
import json
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, F
from .forms import *
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your views here.

# def user_order_list(request):
#     """ List all orders with related items """
#     orders = Order.objects.prefetch_related("items__product").filter(created_by_id=request.user.id)
#     return render(request, "user/user_orders_list.html", {"orders": orders})

def admin_order_list(request):
    """ List all orders with related items """
    orders = Order.objects.prefetch_related("items__product").all()
    return render(request, "users_orders_list.html", {"orders": orders})


def user_order_list(request):
    """ List all orders with related items """
    orders = Order.objects.prefetch_related("items__product").filter(created_by_id=request.user.id)
    return render(request, "user/users_orders_list.html", {"orders": orders})

def order_detail(request, order_id):
    """ Show details of a specific order """
    order = get_object_or_404(Order, id=order_id, created_by=request.user)
    return render(request, "user/order_detail.html", {"order": order})

@login_required
def user_query_list(request):
    try:
        queries = Query.objects.filter(created_by=request.user.id)
        return render(request, 'user/user_query_list.html', {'queries': queries})
    except Exception as e:
        messages.error(request, f"Error fetching queries: {e}")
        return render(request, 'user/user_query_list.html', {'queries': []})  


@login_required
def user_query_create(request):
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
                return redirect('user_query_list')
            except Exception as e:
                messages.error(request, f"Error submitting query: {e}")
    else:
        form = QueryForm()
    return render(request, 'user/query_form.html', {'form': form})

@login_required
def user_query_update(request, pk):
    query = get_object_or_404(Query, pk=pk)
    if request.method == 'POST':
        form = QueryForm(request.POST, request.FILES, instance=query)
        if form.is_valid():
            try:
                query = form.save(commit=False)
                query.updated_by = request.user
                query.save()
                messages.success(request, "Query updated successfully!")
                return redirect('user_query_list')
            except Exception as e:
                messages.error(request, f"Error updating query: {e}")
    else:
        form = QueryForm(instance=query)
    return render(request, 'user/query_form.html', {'form': form})


from products.models import UserCategoryProductMarkup

# def user_product_list(request):
#     products = Product.objects.all()
#     name_query = request.GET.get('name', '').strip()
#     Company_query = request.GET.get('company', '').strip()
#     Composition_query = request.GET.get('Composition', '').strip()
#     alpha = request.GET.get('alpha')

#     if name_query:
#         products = products.filter(name__icontains=name_query)

#     if Company_query:
#         products = products.filter(company__icontains=Company_query)

#     if Composition_query:
#         products = products.filter(composition_name__icontains=Composition_query)

#     if alpha:
#         products = products.filter(name__istartswith=alpha)

#     sort = request.GET.get("sort", "name")
#     order = request.GET.get("order", "asc")
#     allowed_fields = ["product_id", "name", "composition_name", "company", "price", "pack_size", "GST", "quantity"]

#     if sort in allowed_fields:
#         sort_field = f"-{sort}" if order == "desc" else sort
#         products = products.order_by(sort_field)

#     user_category = None
#     if request.user.is_authenticated:
#         user_category = request.user.user_category

#     for product in products:
#         # Debug line
#         print(f"{product.name}: {product.quantity}")

#         # Default fallback
#         product.owner_selling_price = None

#         # Lookup selling price if user_category is present
#         if user_category:
#             markup = UserCategoryProductMarkup.objects.filter(user_category=user_category, product=product).first()
#             if markup:
#                 product.owner_selling_price = markup.owner_selling_price

#         # Optional: fallback price
#         product.customer_price = product.get_customer_price(request.user)

#     return render(request, 'customer/user_Product_list.html', {
#         'products': products,
#         'request': request,  # pass request for retaining filters
#         'sort': sort,
#         'order': order,
#     })



from products.models import UserCategoryProductMarkup, Product
from django.shortcuts import render

# def user_product_list(request):
#     # Step 1: Get all products
#     products = Product.objects.all().select_related('product_type')

#     # Step 2: Get user category if user is authenticated
#     user_category = None
#     if request.user.is_authenticated:
#         user_category = request.user.user_category

#     # Step 3: Prepare a mapping of product_id -> markup data
#     product_markup_map = {}
#     if user_category:
#         markups = UserCategoryProductMarkup.objects.filter(
#             user_category=user_category,
#             product__in=products
#         ).select_related('product')

#         product_markup_map = {
#             markup.product_id: markup for markup in markups
#         }

#     # Step 4: Annotate each product with markup info
#     for product in products:
#         markup = product_markup_map.get(product.id)
#         if markup:
#             product.owner_selling_price = markup.owner_selling_price
#             product.retailer_margin_percent = markup.retailer_margin_percent
#         else:
#             product.owner_selling_price = None
#             product.retailer_margin_percent = None

#     # Step 5: Render template
#     return render(request, 'customer/user_Product_list.html', {
#         'products': products,
#     })



def user_product_list(request):
    form=QueryForm()
    user = request.user
    user_category = getattr(user, 'user_category', None)
    print(f"User: {user}, User Category: {user_category}")
    if not user.is_authenticated or not user_category:
        # Optional: redirect or show message
        print("User is not authenticated or does not have a user category.")

    products = Product.objects.all().select_related('product_type')

    # Get markup data for all products for this user category
    markups = UserCategoryProductMarkup.objects.filter(
        user_category=user_category,
        product__in=products
    ).select_related('product')

    product_markup_map = {markup.product.id: markup for markup in markups}

    for product in products:
        markup = product_markup_map.get(product.id)
        if markup:
            product.display_price = markup.owner_selling_price
            product.owner_selling_price = markup.owner_selling_price
            product.retailer_margin = markup.retailer_margin  # Add this line
            product.retailer_margin_percent = markup.retailer_margin_percent
        else:
            product.display_price = None
            product.owner_selling_price = None
            product.retailer_margin = None  # Add this line
            product.retailer_margin_percent = None

    return render(request, 'customer/user_Product_list.html', {
        'products': products,
        'form':form
    })


# def checkout_and_query(request):
#     if request.method == 'POST':
#         user = request.user

#         # Handle cart
#         cart_data = request.POST.get('cart')
#         if cart_data:
#             cart_items = json.loads(cart_data)
#             # TODO: Save cart items in your Order model
#             print("Cart items:", cart_items)

#         # Handle multiple query items
#         query_items = []
#         for key in request.FILES.keys():
#             if key.startswith('Product_image_'):
#                 idx = key.split('_')[2]
#                 description = request.POST.get(f'description_{idx}', '')
#                 business = request.POST.get(f'Business_name_{idx}')
#                 contact = request.POST.get(f'contact_number_{idx}')

#                 generic = request.POST.get(f'generic_{idx}') == 'on'
#                 same_brand = request.POST.get(f'same_brand_{idx}') == 'on'
#                 product_image = request.FILES.get(f'Product_image_{idx}')

#                 if description or product_image:
#                     q = Query.objects.create(
#                         description=description,
#                         Business_name=business,
#                         contact_number=contact or None,
#                         Product_image=product_image,
#                         created_by=user,
#                         updated_by=user,
#                         generic=generic,
#                         same_brand=same_brand
#                     )
#                     query_items.append(q)

#         # Also handle single query if no file
#         total_query_count = len(request.POST.keys())
#         for key in request.POST.keys():
#             if key.startswith('description_') and not key.endswith(tuple(request.FILES.keys())):
#                 idx = key.split('_')[1]
#                 description = request.POST.get(f'description_{idx}')
#                 business = request.POST.get(f'Business_name_{idx}')
#                 contact = request.POST.get(f'contact_number_{idx}')

#                 generic = request.POST.get(f'generic_{idx}') == 'on'
#                 same_brand = request.POST.get(f'same_brand_{idx}') == 'on'
#                 product_image = request.FILES.get(f'Product_image_{idx}')

#                 if description or product_image:
#                     q = Query.objects.create(
#                         description=description,
#                              Business_name=business,
#                         contact_number=contact or None,
#                         Product_image=product_image,
#                         created_by=user,
#                         updated_by=user,
#                         generic=generic,
#                         same_brand=same_brand
#                     )
#                     query_items.append(q)

#         print("Saved query items:", query_items)
#         return JsonResponse({'status':'success'})

#     return JsonResponse({'status':'error', 'message':'Invalid request'})

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def checkout_and_query(request):
    if request.method == 'POST':
        try:
            user = request.user
            cart_data = request.POST.get('cart')
            queries = []

            # --- 1. Cart Order Handling ---
            order = None
            if cart_data:
                cart = json.loads(cart_data)
                if cart:
                    total_price = sum(item['price'] * item['qty'] for item in cart)
                    total_quantity = sum(item['qty'] for item in cart)
                    order = Order.objects.create(
                        total_price=total_price,
                        total_amount=total_price,
                        total_quantity=total_quantity,
                        status='ordered',
                        created_by=user,
                        updated_by=user
                    )

                    for item in cart:
                        product = Product.objects.get(id=item['id'])
                        quantity = int(item['qty'])
                        item_total = Decimal(item['price']) * quantity

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            product_no=product.product_id,
                            quantity=quantity,
                            total_price=item_total,
                            created_by=user,
                            updated_by=user,
                            MRP=product.MRP,
                            user_price=product.price,
                            discount=product.discount,
                            GST=product.GST,
                            batch=product.batch,
                        )

                        # Reduce stock
                        if hasattr(product, 'quantity'):
                            product.quantity -= quantity
                            product.save()

            # --- 2. Query Form Handling ---
            for key in request.POST:
                if key.startswith('Business_name_'):
                    index = key.split('_')[-1]
                    business_name = request.POST.get(f'Business_name_{index}')
                    contact_number = request.POST.get(f'contact_number_{index}')
                    description = request.POST.get(f'description_{index}')
                    generic = request.POST.get(f'generic_{index}') == 'on'
                    same_brand = request.POST.get(f'same_brand_{index}') == 'on'
                    product_image = request.FILES.get(f'Product_image_{index}')

                    q = Query.objects.create(
                        created_by=user,
                        Business_name=business_name,
                        contact_number=contact_number,
                        description=description,
                        generic=generic,
                        same_brand=same_brand,
                        Product_image=product_image
                    )
                    queries.append(q.id)

            return JsonResponse({
                'success': True,
                'order_id': order.id if order else None,
                'queries': queries,
                'message': 'Order and Queries submitted successfully.'
            })

        except Exception as e:
            print("Error:", e)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

#good codec
# def user_product_list(request):
#     user = request.user
#     user_category = getattr(user, 'user_category', None)
#     print(f"User: {user}, User Category: {user_category}")
#     if not user.is_authenticated or not user_category:
#         # Optional: redirect or show message
#         print("User is not authenticated or does not have a user category.")

#     products = Product.objects.all().select_related('product_type')

#     # Get markup data for all products for this user category
#     markups = UserCategoryProductMarkup.objects.filter(
#         user_category=user_category,
#         product__in=products
#     ).select_related('product')

#     product_markup_map = {markup.product.id: markup for markup in markups}

#     for product in products:
#         markup = product_markup_map.get(product.id)
#         product.display_price = markup.owner_selling_price if markup else None

#     return render(request, 'customer/user_Product_list.html', {
#         'products': products,
#     })


# def user_product_list(request):
#     products = Product.objects.all()
#     name_query = request.GET.get('name', '').strip()
#     Company_query = request.GET.get('company', '').strip()
#     Composition_query = request.GET.get('Composition', '').strip()
#     alpha = request.GET.get('alpha')
#     if name_query:
#         products = products.filter(name__icontains=name_query)

#     if Company_query:
#         products = products.filter(company__icontains=Company_query)
    
#     if Composition_query:
#         products = products.filter(composition_name__icontains=Composition_query)

#     if alpha:
#         products = products.filter(name__istartswith=alpha)

#     sort = request.GET.get("sort", "name")
#     order = request.GET.get("order", "asc")
#     allowed_fields = ["product_id", "name", "composition_name", "company", "price", "pack_size", "GST", "quantity"]

#     if sort in allowed_fields:
#         sort_field = f"-{sort}" if order == "desc" else sort
#         products = products.order_by(sort_field)
#     for product in products:
#         print(f"{product.name}: {product.quantity}")  # Debug line

#         product.customer_price = product.get_customer_price(request.user)
#     return render(request, 'customer/user_Product_list.html', {'products': products, "request": request,  # pass request for retaining filters
#         "sort": sort,
#         "order": order,})



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
                    total_amount = item["total"]   # Assuming `cart_items` is available
                else:
                    return JsonResponse({"error": f"Not enough stock for {product.name}"}, status=400)

            OrderItem.objects.bulk_create(order_items)  # Bulk insert order items
            return JsonResponse({"message": "Order placed successfully", "order_id": order.id,
                                     "redirect_url": reverse("invoice_view", args=[order.id]) })

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
                return redirect('admin_orders')
            except Exception as e:
                messages.error(request, f"Error updating order: {e}")
    else:
        form = OrderForm(instance=order)
    return render(request, 'productss/order_form.html', {'form': form})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt




# @csrf_exempt
# @login_required
# def place_order(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             print('---',data)
#             print('----',request.user)
#             # Create the order
#             order = Order(
#                 total_quantity=data['total_quantity'],
#                 total_price=data['total_price'],
#                 total_amount=data['total_price'],  # Assuming no taxes/discounts for now
#                 status='ordered',
#                 created_by=request.user,
#                 updated_by=request.user
#             )
#             order.save()
#             print('--order-',order)
#             # Create order items
#             for item_data in data['items']:
#                 product = Product.objects.get(id=item_data['product_id'])
#                 product_name = f"{product.name} - {product.composition_name}" if product.composition_name else product.name
#                 product_no=product.product_id
#                 OrderItem.objects.create(
#                     order=order,
#                     product=product,
#                     product_name=product_name,
#                     product_id=product_no,
#                     quantity=item_data['quantity'],
#                     total_price=item_data['total_price'],
#                     created_by=request.user,
#                     updated_by=request.user
#                 )
#                 product('---order---',OrderItem)
#                 # Update product quantity (optional)
#                 product.quantity -= item_data['quantity']
#                 product.save()
#                 print('product',product)
#             user = get_object_or_404(User, id=request.user.id)
#             total_amount = item_data["total_price"]   # Assuming `cart_items` is available
        
#             point_allocation = PointAllocation.objects.filter(
#                 Q(min_amount__lte=total_amount) & 
#                 (Q(max_amount__gte=total_amount) | Q(max_amount__isnull=True))
#             ).first()

#             # Assign points if a range is found
#             user.points += point_allocation.points if point_allocation else 0
#             user.save()
#             return JsonResponse({'success': True, 'order_id': order.id})
        
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
#     return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)



# @csrf_exempt
# @login_required
# def place_order(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             print('Received data:', data)
#             print('User:', request.user)

#             # Create the order
#             order = Order(
#                 total_quantity=data['total_quantity'],
#                 total_price=data['total_price'],
#                 total_amount=data['total_price'],  # Assuming no taxes/discounts for now
#                 status='ordered',
#                 created_by=request.user,
#                 updated_by=request.user
#             )
#             order.save()
#             item_lines = []

#             print('Order created:', order)
#             for item_data in data['items']:
#                 # Get the product by id
#                 print('----',item_data['product_id'])
#                 product = Product.objects.get(id=item_data['product_id'])
#                 product_name = f"{product.name} - {product.composition_name}" if product.composition_name else product.name
#                 product_no = product.product_id

#                 print(order,product_no,product_name,)
#                 # Create the OrderItem
#                 order_item = OrderItem.objects.create(
#                     order=order,
#                     product_id=product.pk,
#                     product_name=product_name,
#                     product_no=product_no,
#                     quantity=item_data['quantity'],
#                     total_price=item_data['total_price'],
#                     created_by=request.user,
#                     updated_by=request.user
#                 )
#                 print('OrderItem created:', order_item)

#                 # Update product quantity (if relevant)
#                 if hasattr(product, 'quantity'):
#                     product.quantity -= item_data['quantity']
#                     product.save()
#                     print('Product updated:', product)


               

#             # user = get_object_or_404(User, id=request.user.id)
#             # total_amount = item_data["total_price"]  # Assuming `cart_items` is available

#             # Check for point allocation
#             # point_allocation = PointAllocation.objects.filter(
#             #     Q(min_amount__lte=total_amount) &
#             #     (Q(max_amount__gte=total_amount) | Q(max_amount__isnull=True))
#             # ).first()

#             # if point_allocation:
#             #     print(f"Point allocation found: {point_allocation.points} points")
#             #     user.points += point_allocation.points
#             #     user.save()
#             # else:
#             #     print("No point allocation found")

#             return JsonResponse({'success': True, 'order_id': order.id})

#         except Exception as e:
#             print("Error occurred:", e)
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)

#     return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


# @csrf_exempt
# @login_required
# def place_order(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             print('Received data:', data)
#             print('User:', request.user)

#             # Create the order
#             order = Order(
#                 total_quantity=data.get('total_quantity', sum(item['quantity'] for item in data['items'])),
#                 total_price=data['total_price'],
#                 total_amount=data['total_price'],
#                 status='ordered',
#                 created_by=request.user,
#                 updated_by=request.user
#             )
#             order.save()
            
#             item_lines = []

#             print('Order created:', order)
#             for item_data in data['items']:
#                 try:
#                     product = Product.objects.get(id=item_data['product_id'])
#                     product_name = f"{product.name} - {product.composition_name}" if product.composition_name else product.name
#                     product_no = product.product_id

#                     print(order, product_no, product_name)
#                     # Create the OrderItem
#                     order_item = OrderItem.objects.create(
#                         order=order,
#                         product_id=product.pk,
#                         product_name=product_name,
#                         product_no=product_no,
#                         quantity=item_data['quantity'],
#                         total_price=item_data['total_price'],
#                         created_by=request.user,
#                         updated_by=request.user
#                     )
#                     print('OrderItem created:', order_item)

#                     # Update product quantity (if relevant)
#                     if hasattr(product, 'quantity'):
#                         product.quantity -= item_data['quantity']
#                         product.save()
#                         print('Product updated:', product)

#                 except Product.DoesNotExist:
#                     print(f"Product with id {item_data['product_id']} not found")
#                     continue

#             return JsonResponse({'success': True, 'order_id': order.id})

#         except Exception as e:
#             print("Error occurred:", e)
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)

#     return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


from decimal import Decimal
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

@csrf_exempt
@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user
            print('Received data:', data)

            # Create Order
            order = Order.objects.create(
                total_quantity=data.get('total_quantity', sum(item['quantity'] for item in data['items'])),
                total_price=data['total_price'],
                total_amount=data['total_price'],
                status='ordered',
                created_by=user,
                updated_by=user
            )

            # Initialize totals
            total_gst = Decimal('0.00')
            total_discount = Decimal('0.00')
            actual_total = Decimal('0.00')
            retailer_sale_total = Decimal('0.00')
            retailer_purchase_total = Decimal('0.00')
            admin_profit = Decimal('0.00')

            user_category = getattr(user, 'user_category', None)

            for item_data in data['items']:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = item_data['quantity']
                item_total = item_data['total_price']

                # Get markup before using selling price or GST
                markup = UserCategoryProductMarkup.objects.filter(
                    user_category=user_category,
                    product=product
                ).first() if user_category else None

                # Owner selling price and GST
                owner_selling_price = markup.owner_selling_price if markup else product.price or 0
                GST_percent = product.GST or 0

                # Billing values
                gst_amt = ((owner_selling_price * GST_percent) / 100) * quantity
                discount_amt = ((product.MRP or 0) * (product.discount or 0) / 100) * quantity
                actual_amt = (product.MRP or 0) * quantity

                # Retailer purchase/sale/profit
                retailer_purchase = owner_selling_price * quantity
                retailer_sale = (product.MRP or 0) * quantity
                retailer_profit = retailer_sale - retailer_purchase
                admin_profit_amt = retailer_purchase - ((product.price or 0) * quantity)

                # Save order item
                product_name = f"{product.name} - {product.composition_name}" if product.composition_name else product.name

                OrderItem.objects.create(
                product_no = product.product_id,
                    order=order,
                    product=product,
                    product_name=product_name,
                    # product_no=product.product_id,
                    quantity=quantity,
                    total_price=item_total,
                    created_by=user,
                    updated_by=user,
                    GST=product.GST,
                    MRP=product.MRP,
                    Batch=product.batch,
                    user_price = product.price * Decimal('1.10'),
                    discount=product.discount,
     
                )

                # Update inventory
                if hasattr(product, 'quantity'):
                    product.quantity -= quantity
                    product.save()

                # Accumulate billing totals
                total_gst += gst_amt
                total_discount += discount_amt
                actual_total += actual_amt
                retailer_sale_total += retailer_sale
                retailer_purchase_total += retailer_purchase
                admin_profit += admin_profit_amt

            # Save billing
            OrderBilling.objects.create(
                order=order,
                total_gst=total_gst,
                total_discount=total_discount,
                actual_total=actual_total,
                retailer_sale_total=retailer_sale_total,
                retailer_purchase_total=retailer_purchase_total,
                retailer_profit=retailer_sale_total - retailer_purchase_total,
                admin_profit=admin_profit,
                outstanding_amount=retailer_purchase_total,
                created_by=user
            )

            return JsonResponse({'success': True, 'order_id': order.id})

        except Exception as e:
            print("Error occurred:", e)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def customer_order_list(request):
    try:
        statuses = OrderItemsMain.objects.select_related('order').all()
        return render(request, 'user/customer_order_list.html', {'statuses': statuses})
    except Exception as e:
        messages.error(request, f"Error fetching statuses: {e}")
        return redirect('customer_order_list')
    
    

# def customer_order_create(request):
#     if request.method == 'POST':
#         # Create the form and formset instances from the POST data
#         form = CustomerOrderForm(request.POST)
#         formset = OrderItemTempFormSet(request.POST)

#         # Check if the CustomerOrder form is valid
#         if form.is_valid():
#             # Save the CustomerOrder instance (but don't commit to DB yet)
#             order = form.save(commit=False)
#             order.created_by = request.user  # Associate the order with the logged-in user
#             order.save()  # Save the CustomerOrder instance
#             # Set the foreign key for the order items
#             for order_item_form in formset:
#                 # Associate each OrderItem form with the saved order
#                 order_item_form.instance.order = order
#             # Check if the formset is valid
#             if formset.is_valid():
#                 formset.save()  # Save all related OrderItems
#                 OrderItems.objects.create(
#                      order = formset.order,
#     product_name =formset.product_name,
#     generic = formset.generic,
#     same_brand = formset.same_brand,
#     quantity = formset.quantity,
#     notes = formset.notes

#                 )
#                 messages.success(request, "Order saved successfully!")  # Success message
#                 return redirect('customer_order_list')  # Redirect to the order list page
#             else:
#                 # Debug: Print formset errors if any
#                 print(formset.errors)
#         else:
#             # Debug: Print form errors if the CustomerOrder form is not valid
#             print(form.errors)

#     else:
#         # Initialize an empty CustomerOrderForm and OrderItemFormSet
#         form = CustomerOrderForm()
#         formset = OrderItemTempFormSet(queryset=OrderItems.objects.none())  # Empty formset initially

#     return render(request, 'user/customer_order_form.html', {
#         'form': form,
#         'formset': formset
#     })

def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def add_to_temp(request):
    if request.method == 'POST':
        form = OrderItemTempForm(request.POST)
        if form.is_valid():
            temp_item = form.save(commit=False)
            temp_item.session_key = get_session_key(request)
            temp_item.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def create_order(request):
    session_key = get_session_key(request)
    temp_items = OrderItemTemp.objects.filter(session_key=session_key)
    
    if request.method == 'POST':
        order_form = CustomerOrderForm(request.POST)
        print(order_form)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            order.customer_name=request.POST.get('customer_name')
            order.number=request.POST.get('number')
            order.save()
            print('order',order.pk)
            # Move items from temp to main
            for temp_item in temp_items:
                OrderItemMain.objects.create(
                    order=order,
                    product_name=temp_item.product_name,
                    product_type=temp_item.product_type,
                    quantity=temp_item.quantity,
                    notes=temp_item.notes
                )
            
            # Clear temp items
            temp_items.delete()
            
            messages.success(request, "Order created successfully!")
            return redirect('customer_order_list')
    
    else:
        order_form = CustomerOrderForm()
    
    return render(request, 'user/create_order.html', {
        'order_form': order_form,
        'temp_items': temp_items,
        'item_form': OrderItemTempForm()
    })

def remove_temp_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        try:
            item = OrderItemTemp.objects.get(id=item_id, session_key=get_session_key(request))
            item.delete()
            return JsonResponse({'success': True})
        except OrderItemTemp.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def customer_order_update(request, pk):
    status = get_object_or_404(CustomerOrder, pk=pk)
    if request.method == 'POST':
        form = CustomerOrderForm(request.POST, instance=status)
        if form.is_valid():
            try:
                status = form.save(commit=False)
                status.updated_by = request.user  
                status.save()
                messages.success(request, "Status updated successfully!")
                return redirect('customer_order_list')
            except Exception as e:
                messages.error(request, f"Error updating status: {e}")
    else:
        form = CustomerOrderForm(instance=status)
    return render(request, 'user/customer_order_form.html', {'form': form})

@login_required
def customer_order_delete(request, pk):
    try:
        status = get_object_or_404(OrderItemMain, pk=pk)
        order = get_object_or_404(CustomerOrder, pk=status.order)
        status.delete()
        order.delete()
        messages.success(request, "Status deleted successfully!")
        return redirect('customer_order_list')
    except Exception as e:
        messages.error(request, f"Error deleting status: {e}")

@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    user=get_object_or_404(User,pk=order.created_by.id)
    subtotal = sum(item.total_price for item in order_items)
    total_quantity = sum(item.quantity for item in order_items)
    # Optional: calculate savings, taxes, etc. if needed

    context = {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "total_quantity": total_quantity,
        "date_time": order.created_at,  # if Order has a created_at field
        "user":user
    }
    return render(request, "customer/invoice.html", context)



