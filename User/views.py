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
from django.utils.dateparse import parse_date
from django.db.models import Q

# Create your views here.

# def user_order_list(request):
#     """ List all orders with related items """
#     orders = Order.objects.prefetch_related("items__product").filter(created_by_id=request.user.id)
#     return render(request, "user/user_orders_list.html", {"orders": orders})


# def admin_order_list(request):
#     """List all orders with related items, with filters for customer name and date range."""
#     orders = Order.objects.prefetch_related("items__product").all()

#     # Get filter values
#     customer = request.GET.get("customer", "").strip()
#     start_date = request.GET.get("start_date", "")
#     end_date = request.GET.get("end_date", "")

#     # 🔹 Filter by customer name (first OR last)
#     if customer:
#         orders = orders.filter(
#             Q(created_by__first_name__icontains=customer) |
#             Q(created_by__last_name__icontains=customer)
#         )

#     # 🔹 Filter by date range
#     if start_date:
#         orders = orders.filter(created_at__date__gte=parse_date(start_date))
#     if end_date:
#         orders = orders.filter(created_at__date__lte=parse_date(end_date))

#     # Optional: sort newest first
#     orders = orders.order_by("-created_at")

#     return render(request, "users_orders_list.html", {"orders": orders})

def admin_order_list(request):
    """List all orders with related items, with filters for customer name and date range."""
    orders = (
        Order.objects
        .select_related("created_by")
        .prefetch_related("items__product", "queries")  # queries = related_name on Query.order
        .all()
    )
    # Filters
    customer = request.GET.get("customer", "").strip()
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    if customer:
        orders = orders.filter(
            Q(created_by__first_name__icontains=customer) |
            Q(created_by__last_name__icontains=customer)
        )

    if start_date:
        orders = orders.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        orders = orders.filter(created_at__date__lte=parse_date(end_date))

    orders = orders.order_by("-created_at")

    return render(request, "users_orders_list.html", {"orders": orders})


def admin_order_issue(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
            "queries__items",
        ),
        pk=order_id
    )

    errors = []

    if request.method == "POST":
        action = request.POST.get("action")

        # ------------- ACTION 1: PACK SELECTED ORDER ITEMS -------------
        if action == "issue_items":
            selected_ids = []
            for key in request.POST.keys():
                if key.startswith("order_item_"):
                    try:
                        selected_ids.append(int(key.split("_")[-1]))
                    except ValueError:
                        pass

            items = OrderItem.objects.filter(order=order, id__in=selected_ids)

            for item in items:
                field_name = f"issue_qty_{item.id}"
                try:
                    issue_qty = int(request.POST.get(field_name, "0"))
                except ValueError:
                    errors.append(f"Invalid quantity for item {item.product_name}.")
                    continue

                ordered_qty = item.quantity

                if issue_qty > ordered_qty:
                    errors.append(
                        f"Item {item.product_name}: Issue qty ({issue_qty}) cannot be greater than ordered qty ({ordered_qty})."
                    )
                elif issue_qty < ordered_qty:
                    errors.append(
                        f"Item {item.product_name}: Issue qty ({issue_qty}) cannot be less than ordered qty ({ordered_qty})."
                    )
                else:
                    # Valid, mark as packed
                    item.status = "packed"
                    item.save()

            # If no errors, optionally update order status if all items packed
            if not errors:
                if not order.items.exclude(status="packed").exists():
                    order.status = "packed"
                    order.save()

        # ------------- ACTION 2: CONVERT SELECTED QUERY ITEMS -------------
        elif action == "convert_query_items":
            selected_ids = []
            for key in request.POST.keys():
                if key.startswith("query_item_"):
                    try:
                        selected_ids.append(int(key.split("_")[-1]))
                    except ValueError:
                        pass

            qitems = QueryItem.objects.filter(query__order=order, id__in=selected_ids)

            for qi in qitems:
                field_name = f"query_issue_qty_{qi.id}"
                try:
                    issue_qty = int(request.POST.get(field_name, "0"))
                except ValueError:
                    errors.append(f"Invalid quantity for query item {qi.product_name}.")
                    continue

                if issue_qty <= 0:
                    errors.append(f"Query item {qi.product_name}: Issue qty must be > 0.")
                    continue

                if issue_qty > qi.pending_qty and qi.pending_qty > 0:
                    errors.append(
                        f"Query item {qi.product_name}: Issue qty ({issue_qty}) cannot be greater than pending qty ({qi.pending_qty})."
                    )
                    continue

                # Find or create corresponding OrderItem
                # Match on product if present, else product_name
                order_item = None
                if qi.product:
                    order_item, created = OrderItem.objects.get_or_create(
                        order=order,
                        product=qi.product,
                        defaults={
                            "product_name": qi.product.name,
                            "product_no": getattr(qi.product, "product_id", ""),
                            "quantity": 0,
                            "total_price": Decimal("0.00"),
                            "status": "packed",  # directly packed
                        },
                    )
                else:
                    order_item, created = OrderItem.objects.get_or_create(
                        order=order,
                        product=None,
                        product_name=qi.product_name,
                        defaults={
                            "product_no": "",
                            "quantity": 0,
                            "total_price": Decimal("0.00"),
                            "status": "packed",
                        },
                    )

                # Update quantities & price
                order_item.quantity += issue_qty
                # If you have price in product, use it; else keep old
                unit_price = getattr(qi.product, "price", None) if qi.product else None
                if unit_price is None and order_item.quantity > 0:
                    # Keep existing average
                    pass
                else:
                    order_item.total_price = (unit_price or Decimal("0")) * order_item.quantity

                order_item.status = "packed"
                order_item.save()

                # Update QueryItem (we'll delete on full issue)
                qi.issued_qty += issue_qty
                qi.save()
                if qi.pending_qty == 0:
                    qi.delete()

            # Recalculate order totals
            if not errors:
                all_items = order.items.all()
                order.total_quantity = sum(i.quantity for i in all_items)
                order.total_price = sum(i.total_price for i in all_items)
                order.total_amount = order.total_price  # if same
                order.save()

        # After POST (either action), reload with updated data
        # (fall through to render below)

    # Prepare data for GET / after POST
    pending_items = order.items.exclude(status="packed")
    packed_items = order.items.filter(status="packed")

    queries = order.queries.prefetch_related("items").all()
    query_items = QueryItem.objects.filter(query__order=order)

    return render(request, "order_issue.html", {
        "order": order,
        "pending_items": pending_items,
        "packed_items": packed_items,
        "queries": queries,
        "query_items": query_items,
        "errors": errors,
    })


# def user_order_list(request):
#     """ List all orders with related items """
#     orders = Order.objects.prefetch_related("items__product").filter(created_by_id=request.user.id)
#     orders = orders.order_by("-created_at")

#     return render(request, "user/users_orders_list.html", {"orders": orders})

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



@login_required
def user_product_list(request):
    form = QueryForm()
    user = request.user
    user_category = getattr(user, 'user_category', None)

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

            # load temp cart & temp queries for this user
    # Temp cart + queries + header
    cart_items = TempCartItem.objects.filter(user=user).select_related('product')
    query_items = TempQueryItem.objects.filter(user=user).select_related('product')
    query_header = TempQueryHeader.objects.filter(user=user).first()

    cart_subtotal = sum(ci.total_price for ci in cart_items) if cart_items else 0
    cart_item_count = cart_items.count()
    cart_total_qty = sum(ci.quantity for ci in cart_items) if cart_items else 0


    return render(request, 'customer/user_Product_list.html', {
        'products': products,
        'form':form,
        'cart_items': cart_items,
        'query_items': query_items,
        'query_header': query_header,
        'cart_subtotal': cart_subtotal,
        'cart_item_count': cart_item_count,
        'cart_total_qty': cart_total_qty,
    })

def _add_to_temp_query(user, product, requested_qty, reason=None):
    if requested_qty <= 0:
        return
    q_item, created = TempQueryItem.objects.get_or_create(
        user=user,
        product=product,
        defaults={
            'product_name': product.name,
            'requested_qty': 0,
            'reason': reason or 'OUT_OF_STOCK'
        }
    )
    q_item.requested_qty += requested_qty
    if reason:
        q_item.reason = reason
    q_item.save()
    
    
    
    
from django.views.decorators.http import require_POST



@require_POST
@login_required
def ajax_add_to_cart(request):
    user = request.user
    product_id = request.POST.get('product_id')
    qty = int(request.POST.get('qty', 1))

    product = get_object_or_404(Product, id=product_id)
    available = int(getattr(product, 'quantity', 0))

    # No stock -> everything to missed products
    if available <= 0:
        _add_to_temp_query(user, product, qty, reason="OUT_OF_STOCK")
        return _cart_and_query_response(user)

    cart_item, created = TempCartItem.objects.get_or_create(
        user=user,
        product=product,
        defaults={'unit_price': product.price, 'quantity': 0}
    )

    desired_total_qty = cart_item.quantity + qty

    if desired_total_qty <= available:
        cart_item.quantity = desired_total_qty
        cart_item.unit_price = product.price
        cart_item.save()
    else:
        remainder = desired_total_qty - available
        cart_item.quantity = available
        cart_item.unit_price = product.price
        cart_item.save()
        _add_to_temp_query(user, product, remainder, reason="PARTIAL_STOCK")

    return _cart_and_query_response(user)



@require_POST
@login_required
def ajax_remove_cart_item(request):
    user = request.user
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)

    TempCartItem.objects.filter(user=user, product=product).delete()
    return _cart_and_query_response(user)


def _cart_and_query_response(user):
    cart_items = TempCartItem.objects.filter(user=user).select_related('product')
    query_items = TempQueryItem.objects.filter(user=user).select_related('product')

    cart_list = []
    subtotal = Decimal('0.00')
    total_qty = 0
    for ci in cart_items:
        subtotal += ci.total_price
        total_qty += ci.quantity
        cart_list.append({
            'product_id': ci.product.id,
            'name': ci.product.name,
            'qty': ci.quantity,
            'available_quantity': int(getattr(ci.product, 'quantity', 0)),
            'unit_price': float(ci.unit_price),
            'total_price': float(ci.total_price),
        })

    query_list = []
    for qi in query_items:
        query_list.append({
            'id': qi.id,
            'product_id': qi.product.id if qi.product else None,
            'product_name': qi.product_name,
            'requested_qty': qi.requested_qty,
            'reason': qi.reason,
        })

    return JsonResponse({
        'success': True,
        'cart': cart_list,
        'cart_subtotal': float(subtotal),
        'cart_total_qty': total_qty,
        'cart_item_count': len(cart_list),
        'query_items': query_list,
    })
@require_POST
@login_required
def ajax_remove_temp_query_item(request):
    user = request.user
    query_id = request.POST.get('query_id')
    TempQueryItem.objects.filter(user=user, id=query_id).delete()
    return _cart_and_query_response(user)



@require_POST
@login_required
def ajax_update_temp_query_qty(request):
    user = request.user
    query_id = request.POST.get('query_id')
    qty = int(request.POST.get('qty', 0))

    try:
        tq = TempQueryItem.objects.get(user=user, id=query_id)
    except TempQueryItem.DoesNotExist:
        return _cart_and_query_response(user)

    if qty <= 0:
        tq.delete()
    else:
        tq.requested_qty = qty
        tq.save()

    return _cart_and_query_response(user)


@require_POST
@login_required
def ajax_save_query_header(request):
    user = request.user
    business_name = request.POST.get('business_name', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    description = request.POST.get('description', '').strip()

    header, created = TempQueryHeader.objects.get_or_create(user=user)
    header.business_name = business_name
    header.contact_number = contact_number
    header.description = description
    header.save()

    return JsonResponse({'success': True})


@require_POST
@login_required
def ajax_update_cart_qty(request):
    user = request.user
    product_id = request.POST.get('product_id')
    qty = int(request.POST.get('qty', 0))

    product = get_object_or_404(Product, id=product_id)
    available = int(getattr(product, 'quantity', 0))

    try:
        cart_item = TempCartItem.objects.get(user=user, product=product)
    except TempCartItem.DoesNotExist:
        if qty > 0:
            request.POST = request.POST.copy()
            request.POST['qty'] = qty
            return ajax_add_to_cart(request)
        return _cart_and_query_response(user)

    if qty <= 0:
        _add_to_temp_query(user, product, cart_item.quantity, reason="QTY_ZERO")
        cart_item.delete()
        return _cart_and_query_response(user)

    if qty <= available:
        cart_item.quantity = qty
        cart_item.unit_price = product.price
        cart_item.save()
        return _cart_and_query_response(user)

    remainder = qty - available
    cart_item.quantity = available
    cart_item.unit_price = product.price
    cart_item.save()
    _add_to_temp_query(user, product, remainder, reason="PARTIAL_STOCK")
    return _cart_and_query_response(user)


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


# @csrf_exempt
# @login_required
# def checkout_and_query(request):
#     if request.method == 'POST':
#         try:
#             user = request.user
#             cart_data = request.POST.get('cart')
#             queries = []

#             # --- 1. Cart Order Handling ---
#             order = None
#             if cart_data:
#                 cart = json.loads(cart_data)
#                 if cart:
#                     total_price = sum(item['price'] * item['qty'] for item in cart)
#                     total_quantity = sum(item['qty'] for item in cart)
#                     order = Order.objects.create(
#                         total_price=total_price,
#                         total_amount=total_price,
#                         total_quantity=total_quantity,
#                         status='ordered',
#                         created_by=user,
#                         updated_by=user
#                     )

#                     for item in cart:
#                         product = Product.objects.get(id=item['id'])
#                         quantity = int(item['qty'])
#                         item_total = Decimal(item['price']) * quantity

#                         OrderItem.objects.create(
#                             order=order,
#                             product=product,
#                             product_name=product.name,
#                             product_no=product.product_id,
#                             quantity=quantity,
#                             total_price=item_total,
#                             created_by=user,
#                             updated_by=user,
#                             MRP=product.MRP,
#                             user_price=product.price,
#                             discount=product.discount,
#                             GST=product.GST,
#                             batch=product.batch,
#                         )

#                         # Reduce stock
#                         if hasattr(product, 'quantity'):
#                             product.quantity -= quantity
#                             product.save()

#             # --- 2. Query Form Handling ---
#             for key in request.POST:
#                 if key.startswith('Business_name_'):
#                     index = key.split('_')[-1]
#                     business_name = request.POST.get(f'Business_name_{index}')
#                     contact_number = request.POST.get(f'contact_number_{index}')
#                     description = request.POST.get(f'description_{index}')

#                     q = Query.objects.create(
#                         created_by=user,
#                         Business_name=business_name,
#                         contact_number=contact_number,
#                         description=description,
#                     )
#                     queries.append(q.id)

#             return JsonResponse({
#                 'success': True,
#                 'order_id': order.id if order else None,
#                 'queries': queries,
#                 'message': 'Order and Queries submitted successfully.'
#             })

#         except Exception as e:
#             print("Error:", e)
#             return JsonResponse({'success': False, 'error': str(e)}, status=400)

#     return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def checkout_and_query(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

    user = request.user

    try:
        # ---- 1. Temp cart -> Order ----
        temp_cart = TempCartItem.objects.filter(user=user).select_related('product')
        if not temp_cart.exists():
            order = None
        else:
            total_price = sum(ci.total_price for ci in temp_cart)
            total_quantity = sum(ci.quantity for ci in temp_cart)

            order = Order.objects.create(
                total_price=total_price,
                total_amount=total_price,
                total_quantity=total_quantity,
                status='ordered',
                created_by=user,
                updated_by=user
            )

            for ci in temp_cart:
                product = ci.product
                quantity = ci.quantity
                item_total = ci.total_price

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

                if hasattr(product, 'quantity'):
                    product.quantity = max(0, product.quantity - quantity)
                    product.save()

            temp_cart.delete()

        # ---- 2. Temp header + TempQueryItem -> Query + QueryItem ----
        temp_queries = TempQueryItem.objects.filter(user=user)

        # Update header from POST (latest values)
        business_name = request.POST.get('business_name', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        description = request.POST.get('missed_description', '').strip()

        header, _ = TempQueryHeader.objects.get_or_create(user=user)
        if business_name:
            header.business_name = business_name
        if contact_number:
            header.contact_number = contact_number
        if description:
            header.description = description
        header.save()

        # Which temp query items selected via checkbox?
        selected_ids = []
        for key in request.POST.keys():
            if key.startswith('query_item_selected_'):
                try:
                    selected_ids.append(int(key.split('_')[-1]))
                except ValueError:
                    continue

        selected_temp_queries = temp_queries.filter(id__in=selected_ids)

        if selected_temp_queries.exists():
            query_header = Query.objects.create(
                order=order,
                created_by=user,
                updated_by=user,
                Business_name=header.business_name or '',
                contact_number=header.contact_number or '',
                description=header.description or 'Missed products / queries from checkout',
            )

            for tq in selected_temp_queries:
                QueryItem.objects.create(
                    query=query_header,
                    product=tq.product,
                    product_name=tq.product_name,
                    requested_qty=tq.requested_qty,
                    issued_qty=0,
                    status='pending',
                )

        # Clear temp header & temp queries
        TempQueryHeader.objects.filter(user=user).delete()
        temp_queries.delete()

        return JsonResponse({
            'success': True,
            'order_id': order.id if order else None,
            'message': 'Order and Queries submitted successfully.'
        })

    except Exception as e:
        print("Error:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

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

# def order_list(request):
#     """ List all orders with related items """
#     orders = Order.objects.prefetch_related("items__product").all()
#     return render(request, "productss/orders_list.html", {"orders": orders})


def order_list(request):
    orders = (
        Order.objects
        .select_related('created_by')
        .prefetch_related('items__product', 'queries')
        .all()
    )
    return render(request, "productss/orders_list.html", {"orders": orders})

# products/views.py

def order_invoice(request, pk):
    """
    Show order header, items, and any related Query + QueryItems
    """
 # only if not already imported

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
            "queries__items",   # QueryItem has related_name='items'
        ),
        pk=pk
    )

    queries = order.queries.all()  # because Query.order has related_name='queries'

    return render(request, "productss/order_invoice.html", {
        "order": order,
        "queries": queries,
    })


def admin_order_invoice(request, pk):
    """
    Show order header, items, and any related Query + QueryItems
    """

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
            "queries__items",   # QueryItem has related_name='items'
        ),
        pk=pk
    )

    queries = order.queries.all()  # because Query.order has related_name='queries'

    return render(request, "productss/admin_order_invoice.html", {
        "order": order,
        "queries": queries,
    })


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



