from django.shortcuts import render,redirect
from .models import *
from .forms import *
from django.contrib import messages


def supplier_create(request):
    try:
        pass
    except Exception as e:
        messages.error(request, f"Error fetching countries: {e}")
        return redirect('country_list')