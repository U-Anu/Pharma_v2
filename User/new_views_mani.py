from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.shortcuts import render
from django.urls import reverse
from products.forms import QueryForm
from products.models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from UserManagement.models import *
import json
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, F
from .forms import *
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils.dateparse import parse_date
from django.db.models import Q


@csrf_exempt
@login_required
def checkout_and_query(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

    user = request.user
        # 🔥 ADD YOUR CREDIT LOGIC HERE 👇👇👇

    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    MIN_ORDER_AMOUNT = 1000

    temp_cart = TempCartItem.objects.filter(user=user)
    cart_total = sum(ci.total_price for ci in temp_cart)

    # ✅ 1. Minimum order check
    if cart_total < MIN_ORDER_AMOUNT:
        return JsonResponse({
            'success': False,
            'error': f"Minimum order should be ₹{MIN_ORDER_AMOUNT}"
        })

    # ✅ 2. Used credit

    used_credit = OrderBilling.objects.filter(
        created_by=user,
        is_paid=False
    ).aggregate(total=Sum('outstanding_amount'))['total'] or 0

    # ✅ 3. Overdue check
    today = timezone.now().date()

    overdue_exists = OrderBilling.objects.filter(
        created_by=user,
        is_paid=False,
        credit_due_date__lt=today
    ).exists()

    if overdue_exists:
        return JsonResponse({
            'success': False,
            'error': "Previous credit overdue. Please complete payment."
        })

    # ✅ 4. Credit limit check
    if used_credit + cart_total > user.credit_limit:
        available = user.credit_limit - used_credit
        return JsonResponse({
            'success': False,
            'error': f"Credit limit exceeded. Available: ₹{available}"
        })
        
    from datetime import timedelta
    from django.utils import timezone

    oldest_unpaid = OrderBilling.objects.filter(
        created_by=user,
        is_paid=False
    ).order_by("created_at").first()

    if oldest_unpaid:
        credit_days = user.credit_master.credit_days if user.credit_master else 0

        start_date = oldest_unpaid.created_at.date()
        expiry_date = start_date + timedelta(days=credit_days)

        if timezone.now().date() > expiry_date:
            return JsonResponse({
                'success': False,
                'error': 'Oldest credit bill expired. Please clear dues.'
            })


    try:
        with transaction.atomic():

            # -------------------------------
            # 1. TEMP CART → ORDER
            # -------------------------------
            temp_cart = TempCartItem.objects.filter(user=user).select_related('product')

            order = None
            if temp_cart.exists():
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
                from datetime import timedelta
                credit_days = user.credit_master.credit_days if user.credit_master else 0
                OrderBilling.objects.create(
                    order=order,
                    actual_total=order.total_amount,
                    outstanding_amount=order.total_amount,
                    credit_due_date=timezone.now().date() + timedelta(days=credit_days),
                    created_by=user
                )

                for ci in temp_cart:
                    product = ci.product

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        product_no=product.product_id,
                        quantity=ci.quantity,
                        total_price=ci.total_price,
                        created_by=user,
                        updated_by=user,
                        MRP=product.MRP,
                        user_price=product.price,
                        discount=product.discount,
                        GST=product.GST,
                        batch=product.batch,
                        expiry_date=product.expiry_date,
                    )

                    # Reduce stock safely
                    if hasattr(product, 'quantity') and product.quantity is not None:
                        product.quantity = max(0, product.quantity - ci.quantity)
                        product.save()

                temp_cart.delete()

            # -------------------------------
            # 2. TEMP QUERY → QUERY
            # -------------------------------
            temp_queries = TempQueryItem.objects.filter(user=user)

            business_name = request.POST.get('business_name', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()
            description = request.POST.get(
                'missed_description',
                'Missed products / queries from checkout'
            ).strip()

            # Save temp header (optional but OK)
            header, _ = TempQueryHeader.objects.get_or_create(user=user)
            header.business_name = business_name
            header.contact_number = contact_number
            header.description = description
            header.save()

            # ✅ BEST PRACTICE checkbox handling
            selected_ids = request.POST.getlist('selected_queries')
            selected_temp_queries = temp_queries.filter(id__in=selected_ids)

            # ✅ ALWAYS create Query header
            query_header = Query.objects.create(
                order=order,
                created_by=user,
                updated_by=user,
                Business_name=business_name,
                contact_number=contact_number,
                description=description,
            )

            # Create QueryItems ONLY if selected
            for tq in selected_temp_queries:
                QueryItem.objects.create(
                    query=query_header,
                    product=tq.product,
                    product_name=tq.product_name,
                    requested_qty=tq.requested_qty,
                    issued_qty=0,
                    status='pending',
                )

            # -------------------------------
            # 3. CLEANUP
            # -------------------------------
            TempQueryHeader.objects.filter(user=user).delete()
            temp_queries.delete()

        return JsonResponse({
            'success': True,
            'order_id': order.id if order else None,
            'query_id': query_header.id,
            'message': 'Order and query submitted successfully.'
        })

    except Exception as e:
        print("CHECKOUT ERROR:", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

