from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_label, name='create_label'),
    path('print/<int:id>/', views.print_label, name='print_label'),
    path('add-company/', views.add_company, name='add_company'),
    path('edit-company/<int:id>/', views.edit_company, name='edit_company'),
    path('delete-company/<int:id>/', views.delete_company, name='delete_company'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('edit-customer/<int:id>/', views.edit_customer, name='edit_customer'),
    path('delete-customer/<int:id>/', views.delete_customer, name='delete_customer'),
    path('companies/', views.company_list, name='company_list'),
    path('customers/', views.customer_list, name='customer_list'),
    path('api/add-customer/', views.api_add_customer, name='api_add_customer'),
    path('api/search-customers/', views.api_search_customers, name='api_search_customers'),
]