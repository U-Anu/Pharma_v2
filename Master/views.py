from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from UserManagement.models import PointAllocation
from .models import *
from .forms import *

def country_list(request):
    try:
        countries = Country.objects.all()
        return render(request, 'master/country_list.html', {'countries': countries})
    except Exception as e:
        messages.error(request, f"Error fetching countries: {e}")
        return redirect('country_list')

@login_required
def country_create(request):
    try:
        if request.method == 'POST':
            form = CountryForm(request.POST)
            if form.is_valid():
                try:
                    country = form.save(commit=False)
                    country.created_by = request.user
                    country.save()
                    messages.success(request, "Country added successfully!")
                    return redirect('country_list')
                except Exception as e:
                    messages.error(request, f"Error creating country: {e}")
        else:
            form = CountryForm()
        return render(request, 'master/country_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error fetching countries: {e}")
        return redirect('country_list')

@login_required
def country_update(request, pk):
    try:
        country = get_object_or_404(Country, pk=pk)
        if request.method == 'POST':
            form = CountryForm(request.POST, instance=country)
            if form.is_valid():
                try:
                    country = form.save(commit=False)
                    country.updated_by = request.user
                    country.save()
                    messages.success(request, "Country updated successfully!")
                    return redirect('country_list')
                except Exception as e:
                    messages.error(request, f"Error updating country: {e}")
        else:
            form = CountryForm(instance=country)
        return render(request, 'master/country_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error fetching countries: {e}")
        return redirect('country_list')

@login_required
def country_delete(request, pk):
    try:
        country = get_object_or_404(Country, pk=pk)
        if request.method == 'POST':
            try:
                country.delete()
                messages.success(request, "Country deleted successfully!")
                return redirect('country_list')
            except Exception as e:
                messages.error(request, f"Error deleting country: {e}")
    except Exception as e:
        messages.error(request, f"Error fetching countries: {e}")
        return redirect('country_list')

###############################################################################
@login_required
def dashboard(request):
    pass

##############################################################################

def status_list(request):
    try:
        statuses = UserMemo.objects.all()
        return render(request, 'master/status_list.html', {'statuses': statuses})
    except Exception as e:
        messages.error(request, f"Error fetching statuses: {e}")
        return redirect('status_list')

@login_required
def status_create(request):
    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            try:
                status = form.save(commit=False)
                status.created_by = request.user  
                status.save()
                messages.success(request, "Status added successfully!")
                return redirect('status_list')
            except Exception as e:
                messages.error(request, f"Error creating status: {e}")
    else:
        form = StatusForm()
    return render(request, 'master/status_form.html', {'form': form})


@login_required
def user_memo_create(request,user_id):
    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            try:
                status = form.save(commit=False)
                status.created_by = request.user  
                status.save()
                messages.success(request, "Status added successfully!")
                return redirect('admin_orders')
            except Exception as e:
                messages.error(request, f"Error creating status: {e}")
    else:
        form = StatusForm(initial={'user':user_id})
    return render(request, 'master/status_form.html', {'form': form})

@login_required
def status_update(request, pk):
    status = get_object_or_404(UserMemo, pk=pk)
    if request.method == 'POST':
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            try:
                status = form.save(commit=False)
                status.updated_by = request.user  
                status.save()
                messages.success(request, "Status updated successfully!")
                return redirect('status_list')
            except Exception as e:
                messages.error(request, f"Error updating status: {e}")
    else:
        form = StatusForm(instance=status)
    return render(request, 'master/status_form.html', {'form': form})

@login_required
def status_delete(request, pk):
    try:
        status = get_object_or_404(UserMemo, pk=pk)
        status.delete()
        messages.success(request, "Status deleted successfully!")
        return redirect('status_list')
    except Exception as e:
        messages.error(request, f"Error deleting status: {e}")

@login_required
def user_memo_detail(request, pk):
    memo = get_object_or_404(UserMemo, user__id=pk)

    return render(
        request,
        "master/user_memo_detail.html",
        {"memo": memo}
    )
####################################################################

# Certification Views
def certification_list(request):
    try:
        certifications = Certification.objects.all()
        return render(request, 'master/certification_list.html', {'certifications': certifications})
    except Exception as e:
        messages.error(request, f"Error fetching certifications: {e}")
        return redirect('certification_list')

@login_required
def certification_create(request):
    try:
        if request.method == 'POST':
            form = CertificationForm(request.POST, request.FILES)
            if form.is_valid():
                certificate=form.save(commit=False)
                certificate.created_by=request.user
                certificate.save()
                messages.success(request, "Certification added successfully!")
                return redirect('certification_list')
        else:
            form = CertificationForm()
        return render(request, 'master/certification_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error creating certification: {e}")

@login_required
def certification_update(request, pk):
    certification = get_object_or_404(Certification, pk=pk)
    try:
        if request.method == 'POST':
            form = CertificationForm(request.POST, request.FILES, instance=certification)
            if form.is_valid():
                certificate=form.save(commit=False)
                certificate.updated_by=request.user
                certificate.save()
                messages.success(request, "Certification updated successfully!")
                return redirect('certification_list')
        else:
            form = CertificationForm(instance=certification)
        return render(request, 'master/certification_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error updating certification: {e}")

@login_required
def certification_delete(request, pk):
    try:
        certification = get_object_or_404(Certification, pk=pk)
        certification.delete()
        messages.success(request, "Certification deleted successfully!")
        return redirect('certification_list')
    except Exception as e:
            messages.error(request, f"Error deleting certification: {e}")

# Certification Status Views
def certification_status_list(request):
    try:
        certifications = CertificationStatus.objects.all()
        return render(request, 'master/certification_status_list.html', {'certifications': certifications})
    except Exception as e:
        messages.error(request, f"Error fetching certification statuses: {e}")
        return redirect('certification_status_list')

@login_required
def certification_status_create(request):
    try:
        if request.method == 'POST':
            form = CertificationStatusForm(request.POST, request.FILES)
            if form.is_valid():
                certificate_status=form.save(commit=False)
                certificate_status.created_by=request.user
                certificate_status.save()
                messages.success(request, "Certification status added successfully!")
                return redirect('certification_status_list')
        else:
            form = CertificationStatusForm()
            return render(request, 'master/certification_status_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error creating certification status: {e}")
        return redirect('certification_status_list')

@login_required
def certification_status_update(request, pk):
    certification = get_object_or_404(CertificationStatus, pk=pk)
    try:
        if request.method == 'POST':
            form = CertificationStatusForm(request.POST, request.FILES, instance=certification)
            if form.is_valid():
                certificate_status=form.save(commit=False)
                certificate_status.updated_by=request.user
                certificate_status.save()
                messages.success(request, "Certification status updated successfully!")
                return redirect('certification_status_list')
        else:
            form = CertificationStatusForm(instance=certification)
        return render(request, 'master/certification_status_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error updating certification status: {e}")
        return redirect('certification_status_list')

@login_required
def certification_status_delete(request, pk):
    try:
        certification = get_object_or_404(CertificationStatus, pk=pk)
        certification.delete()
        messages.success(request, "Certification status deleted successfully!")
        return redirect('certification_status_list')
    except Exception as e:
        messages.error(request, f"Error deleting certification status: {e}")
        return redirect('certification_status_list')

# State Views
def state_list(request):
    try:
        states = State.objects.all()
        return render(request, 'master/state_list.html', {'states': states})
    except Exception as e:
        messages.error(request, f"Error fetching states: {e}")
        return redirect('state_list')

@login_required
def state_create(request):
    try:
        if request.method == 'POST':
            form = StateForm(request.POST)
            if form.is_valid():
                state=form.save(commit=False)
                state.created_by=request.user
                state.save()
                messages.success(request, "State added successfully!")
                return redirect('state_list')
        else:
            form = StateForm()
        return render(request, 'master/state_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error creating state: {e}")
        return redirect('state_list')

@login_required
def state_update(request, pk):
    state = get_object_or_404(State, pk=pk)
    try:
        if request.method == 'POST':
            form = StateForm(request.POST, instance=state)
            if form.is_valid():
                state=form.save(commit=False)
                state.upated_by=request.user
                state.save()
                messages.success(request, "State updated successfully!")
                return redirect('state_list')
        else:
            form = StateForm(instance=state)
        return render(request, 'master/state_form.html', {'form': form})
    except Exception as e:
        messages.error(request, f"Error updating state: {e}")
        return redirect('state_list')

@login_required
def state_delete(request, pk):
    try:
        state = get_object_or_404(State, pk=pk)
        state.delete()
        messages.success(request, "State deleted successfully!")
        return redirect('state_list')
    except Exception as e:
        messages.error(request, f"Error deleting state: {e}")
        return redirect('state_list')

# ----------------------------- City CRUD -----------------------------

def city_list(request):
    try:
        cities = City.objects.all()
        return render(request, 'master/city_list.html', {'cities': cities})
    except Exception as e:
        messages.error(request, f"Error fetching cities: {e}")
        return redirect('dashboard')  # Redirect to a safe page

@login_required
def city_create(request):
    form = CityForm(request.POST or None)
    if form.is_valid():
        try:
            city=form.save(commit=False)
            city.created_by=request.user
            city.save()
            messages.success(request, "City added successfully!")
            return redirect('city_list')
        except Exception as e:
            messages.error(request, f"Error creating city: {e}")
    return render(request, 'master/city_form.html', {'form': form})

@login_required
def city_update(request, pk):
    city = get_object_or_404(City, pk=pk)
    form = CityForm(request.POST or None, instance=city)
    if form.is_valid():
        try:
            city=form.save(commit=False)
            city.updated_by=request.user
            city.save()
            messages.success(request, "City updated successfully!")
            return redirect('city_list')
        except Exception as e:
            messages.error(request, f"Error updating city: {e}")
    return render(request, 'master/city_form.html', {'form': form})

@login_required
def city_delete(request, pk):
    try:
        city = get_object_or_404(City, pk=pk)
        city.delete()
        messages.success(request, "City deleted successfully!")
        return redirect('city_list')
    except Exception as e:
            messages.error(request, f"Error deleting city: {e}")



# ----------------------------- Product Category CRUD -----------------------------

def product_category_list(request):
    try:
        categories = ProductCategory.objects.all()
        return render(request, 'master/product_category_list.html', {'categories': categories})
    except Exception as e:
        messages.error(request, f"Error fetching product categories: {e}")

@login_required
def product_category_create(request):
    form = ProductCategoryForm(request.POST or None)
    if form.is_valid():
        try:
            category=form.save(commit=False)
            category.created_by=request.user
            category.save()
            messages.success(request, "Product category added successfully!")
            return redirect('product_category_list')
        except Exception as e:
            messages.error(request, f"Error creating product category: {e}")
    return render(request, 'master/product_category_form.html', {'form': form})

@login_required
def product_category_update(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    form = ProductCategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        try:
            category=form.save(commit=False)
            category.updated_by=request.user
            category.save()
            messages.success(request, "Product category updated successfully!")
            return redirect('product_category_list')
        except Exception as e:
            messages.error(request, f"Error updating product category: {e}")
    return render(request, 'master/product_category_form.html', {'form': form})

@login_required
def product_category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, "Product category deleted successfully!")
            return redirect('product_category_list')
        except Exception as e:
            messages.error(request, f"Error deleting product category: {e}")
    return render(request, 'master/product_category_confirm_delete.html', {'category': category})


# ----------------------------- Schedule Types CRUD -----------------------------

def schedule_types_list(request):
    try:
        schedules = ScheduleTypes.objects.all()
        return render(request, 'master/schedule_types_list.html', {'schedules': schedules})
    except Exception as e:
        messages.error(request, f"Error fetching schedule types: {e}")
        return redirect('dashboard')

@login_required
def schedule_types_create(request):
    form = ScheduleTypesForm(request.POST or None)
    if form.is_valid():
        try:
            scheduletypes=form.save(commit=False)
            scheduletypes.created_by=request.user
            scheduletypes.save()
            messages.success(request, "Schedule type added successfully!")
            return redirect('schedule_types_list')
        except Exception as e:
            messages.error(request, f"Error creating schedule type: {e}")
    return render(request, 'master/schedule_types_form.html', {'form': form})

@login_required
def schedule_types_update(request, pk):
    schedule = get_object_or_404(ScheduleTypes, pk=pk)
    form = ScheduleTypesForm(request.POST or None, instance=schedule)
    if form.is_valid():
        try:
            scheduletypes=form.save(commit=False)
            scheduletypes.updated_by=request.user
            scheduletypes.save()
            messages.success(request, "Schedule type updated successfully!")
            return redirect('schedule_types_list')
        except Exception as e:
            messages.error(request, f"Error updating schedule type: {e}")
    return render(request, 'master/schedule_types_form.html', {'form': form})

@login_required
def schedule_types_delete(request, pk):
    schedule = get_object_or_404(ScheduleTypes, pk=pk)
    if request.method == 'POST':
        try:
            schedule.delete()
            messages.success(request, "Schedule type deleted successfully!")
            return redirect('schedule_types_list')
        except Exception as e:
            messages.error(request, f"Error deleting schedule type: {e}")
    return render(request, 'master/schedule_types_confirm_delete.html', {'schedule': schedule})




# ----------------------------- News Category CRUD -----------------------------

def news_category_list(request):
    """ List all news categories """
    try:
        categories = NewsCategory.objects.all()
        return render(request, 'master/news_category_list.html', {'categories': categories})
    except Exception as e:
        messages.error(request, f"Error fetching news categories: {e}")
        return redirect('dashboard')

@login_required
def news_category_create(request):
    """ Create a new news category """
    form = NewsCategoryForm(request.POST or None)
    if form.is_valid():
        try:
            Category=form.save(commit=False)
            Category.created_by=request.user
            Category.save()
            messages.success(request, "News category added successfully!")
            return redirect('news_category_list')
        except Exception as e:
            messages.error(request, f"Error creating news category: {e}")
    return render(request, 'master/news_category_form.html', {'form': form})

@login_required
def news_category_update(request, pk):
    """ Update an existing news category """
    category = get_object_or_404(NewsCategory, pk=pk)
    form = NewsCategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        try:
            Category=form.save(commit=False)
            Category.updated_by=request.user
            Category.save()
            messages.success(request, "News category updated successfully!")
            return redirect('news_category_list')
        except Exception as e:
            messages.error(request, f"Error updating news category: {e}")
    return render(request, 'master/news_category_form.html', {'form': form})

@login_required
def news_category_delete(request, pk):
    """ Delete a news category """
    category = get_object_or_404(NewsCategory, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, "News category deleted successfully!")
            return redirect('news_category_list')
        except Exception as e:
            messages.error(request, f"Error deleting news category: {e}")
    return render(request, 'master/news_category_confirm_delete.html', {'category': category})

