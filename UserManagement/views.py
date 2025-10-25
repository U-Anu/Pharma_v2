from django.shortcuts import render, redirect

from products.models import Order, OrderItem, Product, Query
from .forms import *
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login as auth_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from datetime import date
import json
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from rest_framework.authtoken.models import Token
from news.models import *
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from products.models import *


def unique_id(pre, last_id):
    today1=date.today()
    today = today1.strftime("%d%m%y")

    last_ids = int(last_id) + 1
    if len(str(last_ids)) == 1:
        id = pre + today + '00' + str(last_ids)
    elif len(str(last_ids)) == 2:
        id = pre + today + '0' + str(last_ids)
    else:
        id = pre + today + str(last_ids)
    return id

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_name=User.objects.get(email=username)
            request.session['name']=user_name.first_name
            user = authenticate(request, username=username, password=password)
            print("user===========",user)
            if user is not None:
                auth_login(request, user)
                messages.success(request, "Login successful! Welcome, {}.".format(username))
                # token, _ = Token.objects.get_or_create(user=user)
                # token_1=token.key
                # print("token_1================",token_1)
                if user.is_customer:
                    customer=user.is_customer
                    print("customer================",customer)
                    return redirect('user_product_list')
                elif user.is_admin or user.is_superuser:
                    adminn=user.is_admin
                    super=user.is_superuser
                    print("admin================",adminn)
                    print("super================",super)
                    return redirect('admin_dash')
                messages.success(request, "Login successful! Welcome, {}.".format(username))
                return redirect('admin_dash')
            else:
                messages.error(request, "Invalid username or password.")  # This line is correct
    else:
        print("hii")
        form = AuthenticationForm()

    return render(request, 'user/login.html', {'form': form})




User = get_user_model()

def approve_user(request, temp_user_id):
    temp_user = get_object_or_404(TempUser, id=temp_user_id)
    user_categories = UserCategory.objects.all()  # Fetch all user categories

    if request.method == "POST":
        user_category_id = request.POST.get("user_category")
        if not user_category_id:
            return render(request, "user/approve_user.html", {
                "temp_user": temp_user,
                "user_categories": user_categories,
                "error": "Please select a user category."
            })

        user_category = get_object_or_404(UserCategory, id=user_category_id)

        # Create and save the user
        user = User.objects.create(
            first_name=temp_user.first_name,
            last_name=temp_user.last_name,
            dob=temp_user.dob,
            address=temp_user.address,
            phone_number=temp_user.phone_number,
            alternate_phone_number=temp_user.alternate_phone_number,
            email=temp_user.email,
            gender=temp_user.gender,
            profile_image=temp_user.profile_image,
            is_admin=False,
            is_customer=True,
            user_category=user_category  # ✅ assign selected category
        )
        user.set_password(temp_user.password)
        user.save()

        temp_user.delete()  # Remove temp record

        return redirect("admin_dash")

    return render(request, "user/approve_user.html", {
        "temp_user": temp_user,
        "user_categories": user_categories
    })

def pending_users(request):
    users = TempUser.objects.filter(is_approved=False)
    return render(request, 'user/user_pending_list.html', {'users': users})


def customer_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            temp_user = TempUser.objects.create(
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                dob=form.cleaned_data['dob'],
                address=form.cleaned_data['address'],
                phone_number=form.cleaned_data['phone_number'],
                alternate_phone_number=form.cleaned_data['alternate_phone_number'],
                email=form.cleaned_data['email'],
                gender=form.cleaned_data['gender'],
                profile_image=form.cleaned_data['profile_image'],
                password=form.cleaned_data['password1'],
                is_approved=False  # Not approved yet
            )
            return redirect('login')  # Redirect to a "waiting for approval" page
    else:
        form = CustomUserCreationForm()
    return render(request, 'user/signup.html', {'form': form})



def admin_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.is_admin = True
            user.is_customer = False
            user.save()
            auth_login(request, user)
            return redirect('admin_dash')
    else:
        form = CustomUserCreationForm()
    return render(request, 'user/admin_create.html', {
        'form': form,
    })

def user_list(request):
    adminn=User.objects.filter(is_admin=False,is_customer=True)
    print("adddddddd",adminn)

    return render(request,"user/user_list.html",{'admin':adminn})

def index(request):
    """List all news articles, grouped by category."""
    articles = NewsArticle.objects.select_related('category').order_by('-published_at')
    # Group articles by category
    categorized_articles = defaultdict(list)
    for article in articles:
        if article.category:
            categorized_articles[article.category.name].append(article)
    products=Product.objects.all().count()
    users=User.objects.all().count()
    orders=Order.objects.all().count()
    return render(request,'index.html',{'articles': dict(categorized_articles),'products':products,'users':users,'orders':orders})

def admin_dash(request):
    users=User.objects.filter(is_customer=True).count()
    pending_users=TempUser.objects.all().count()
    
    products=Product.objects.all().count()
    orders=Order.objects.all().count()
    pending_orders=Order.objects.filter(status='ordered').count()
    delivered_orders=Order.objects.filter(status='delivered').count()
    top_orders=Order.objects.prefetch_related("items__product").order_by("-created_at")[:5]
    queries=Query.objects.all().count()
    return render(request,'admin_dasboard.html',{'users':users,'products':products,'orders':orders,'queries':queries,'pending_orders':pending_orders,'pending_users':pending_users,'top_orders':top_orders})


def user_dash(request):
    username = request.session.get('name', 'Guest')  
    print('username',username)
    products=Product.objects.all().count()
    orders=Order.objects.filter(created_by=request.user).count()
    orders_range=Order.objects.filter(created_by=request.user)
    print('orders',orders_range)
    points=User.objects.get(pk=request.user.id)
    user_points=points.points
    point_table=PointAllocation.objects.all()
    print('point_table',point_table)
    top_orders = Order.objects.filter(created_by=request.user).prefetch_related("items__product").order_by("-created_at")[:5]
    return render(request,'user/user_dasboard.html',{'products':products,'orders':orders,'user_points':user_points,'username':username,'point_table':point_table,'top_orders':top_orders})


def table(request):
    return render(request,'table.html')


def admin_list(request):
    adminn=User.objects.filter(is_staff=True)
    print("adddddddd",adminn)

    return render(request,"user/admin_list.html",{'admin':adminn})


def user_pending_list(request):
    adminn=User.objects.filter(is_admin=True,is_customer=False)
    print("adddddddd",adminn)

    return render(request,"user/user_pending_list.html",{'admin':adminn})

def user_pending_view(request,pk):
    adminn=User.objects.filter(pk=pk)
    print("adddddddd",adminn)
    return render(request,"user/user_pending_view.html",{'user':adminn})


def point_allocation_list_user(request):
    try:
        allocations = PointAllocation.objects.all()
        print("Allocations:", allocations)  # Debugging: Check if QuerySet fetches data
        return render(request, 'user/point_allocation_list_user.html', {'allocations': allocations})
    except Exception as e:
        print(f"Error fetching point allocations: {e}")  # Print error in logs
        messages.error(request, f"Error fetching point allocations: {e}")
        return redirect('point_allocation_list')  # Redirecting to the sa
    
def point_allocation_list(request):
    try:
        allocations = PointAllocation.objects.all()
        print("Allocations:", allocations)  # Debugging: Check if QuerySet fetches data
        return render(request, 'user/point_allocation_list.html', {'allocations': allocations})
    except Exception as e:
        print(f"Error fetching point allocations: {e}")  # Print error in logs
        messages.error(request, f"Error fetching point allocations: {e}")
        return redirect('point_allocation_list')  # Redirecting to the sa

@login_required
def point_allocation_create(request):
    if request.method == 'POST':
        form = PointAllocationForm(request.POST)
        if form.is_valid():
            try:
                allocation = form.save()
                messages.success(request, "Point allocation added successfully!")
                return redirect('point_allocation_list')
            except Exception as e:
                messages.error(request, f"Error creating point allocation: {e}")
    else:
        form = PointAllocationForm()
    return render(request, 'user/point_allocation_form.html', {'form': form})

@login_required
def point_allocation_update(request, pk):
    allocation = get_object_or_404(PointAllocation, pk=pk)
    if request.method == 'POST':
        form = PointAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Point allocation updated successfully!")
                return redirect('point_allocation_list')
            except Exception as e:
                messages.error(request, f"Error updating point allocation: {e}")
    else:
        form = PointAllocationForm(instance=allocation)
    return render(request, 'user/point_allocation_form.html', {'form': form})

@login_required
def point_allocation_delete(request, pk):
    try:
        allocation = get_object_or_404(PointAllocation, pk=pk)
        allocation.delete()
        messages.success(request, "Point allocation deleted successfully!")
        return redirect('point_allocation_list')
    except Exception as e:
        messages.error(request, f"Error deleting point allocation: {e}")



from django.contrib.auth import logout


def logout_view(request):
    logout(request)
    return redirect('login')  