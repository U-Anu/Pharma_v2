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



def order_note_slip(request, pk):
    order = get_object_or_404(Order, pk=pk)
    query = Query.objects.filter(order=order).first()

    # AJAX request → return partial
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'user/order_note_slip_partial.html', {
            'order': order,
            'items': order.items.all(),
            'query': query,
        })

    # fallback (optional)
    return render(request, 'user/order_note_slip.html', {
        'order': order,
        'items': order.items.all(),
        'query': query,
    })