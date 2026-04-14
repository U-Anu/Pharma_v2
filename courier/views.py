from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from openai import models
from .models import Company, Customer, CourierLabel

def create_label(request):
    companies = Company.objects.all().order_by('name')
    customers = Customer.objects.all().order_by('name')

    if request.method == "POST":
        from_company_id = request.POST.get("from_company")
        to_customer_id = request.POST.get("to_customer")
        
        if not from_company_id or not to_customer_id:
            messages.error(request, "Please select both company and customer")
            return render(request, "courier/label_form_alternative.html", {
                "companies": companies,
                "customers": customers
            })
        
        label = CourierLabel.objects.create(
            from_company_id=from_company_id,
            to_customer_id=to_customer_id
        )
        return redirect(f"/courier/print/{label.id}/")

    return render(request, "courier/label_form.html", {
        "companies": companies,
        "customers": customers
    })


def print_label(request, id):
    label = get_object_or_404(CourierLabel, id=id)
    return render(request, "courier/label_print.html", {"label": label})


def company_list(request):
    companies = Company.objects.all().order_by('name')
    return render(request, "courier/company_list.html", {"companies": companies})


def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, "courier/customer_list.html", {"customers": customers})


def add_company(request):
    if request.method == "POST":
        company = Company.objects.create(
            name=request.POST.get("name"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
            phone=request.POST.get("phone"),
        )
        messages.success(request, f"Company '{company.name}' added successfully!")
        return redirect("company_list")
    return render(request, "courier/company_form.html", {"title": "Add Company", "action": "Add"})


def edit_company(request, id):
    company = get_object_or_404(Company, id=id)
    
    if request.method == "POST":
        company.name = request.POST.get("name")
        company.address = request.POST.get("address")
        company.city = request.POST.get("city")
        company.state = request.POST.get("state")
        company.pincode = request.POST.get("pincode")
        company.phone = request.POST.get("phone")
        company.save()
        messages.success(request, f"Company '{company.name}' updated successfully!")
        return redirect("company_list")
    
    return render(request, "courier/company_form.html", {
        "title": "Edit Company",
        "action": "Update",
        "company": company
    })


def delete_company(request, id):
    company = get_object_or_404(Company, id=id)
    
    if request.method == "POST":
        company_name = company.name
        company.delete()
        messages.success(request, f"Company '{company_name}' deleted successfully!")
        return redirect("company_list")
    
    return render(request, "courier/confirm_delete.html", {
        "item": company,
        "type": "Company",
        "cancel_url": "company_list"
    })


def add_customer(request):
    if request.method == "POST":
        customer = Customer.objects.create(
            name=request.POST.get("name"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
            phone=request.POST.get("phone"),
        )
        messages.success(request, f"Customer '{customer.name}' added successfully!")
        return redirect("customer_list")
    return render(request, "courier/customer_form.html", {"title": "Add Customer", "action": "Add"})


def edit_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.address = request.POST.get("address")
        customer.city = request.POST.get("city")
        customer.state = request.POST.get("state")
        customer.pincode = request.POST.get("pincode")
        customer.phone = request.POST.get("phone")
        customer.save()
        messages.success(request, f"Customer '{customer.name}' updated successfully!")
        return redirect("customer_list")
    
    return render(request, "courier/customer_form.html", {
        "title": "Edit Customer",
        "action": "Update",
        "customer": customer
    })


def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    if request.method == "POST":
        customer_name = customer.name
        customer.delete()
        messages.success(request, f"Customer '{customer_name}' deleted successfully!")
        return redirect("customer_list")
    
    return render(request, "courier/confirm_delete.html", {
        "item": customer,
        "type": "Customer",
        "cancel_url": "customer_list"
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Company, Customer, CourierLabel

# ... (keep all your existing functions) ...

@csrf_exempt
@require_http_methods(["POST"])
def api_add_customer(request):
    """API endpoint to add customer via AJAX"""
    try:
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')
        
        # Validation
        if not all([name, address, city, state, pincode, phone]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required'
            })
        
        # Create customer
        customer = Customer.objects.create(
            name=name,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            phone=phone
        )
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'city': customer.city,
                'phone': customer.phone,
                'address': customer.address,
                'state': customer.state,
                'pincode': customer.pincode
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def api_search_customers(request):
    """API endpoint to search customers dynamically"""
    query = request.GET.get('q', '')
    if len(query) >= 2:
        customers = Customer.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(city__icontains=query) |
            models.Q(phone__icontains=query)
        )[:20]
        
        results = [{
            'id': c.id,
            'text': f"{c.name} - {c.city} ({c.phone})",
            'name': c.name,
            'city': c.city,
            'phone': c.phone
        } for c in customers]
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': False}
        })
    
    return JsonResponse({'results': []})
