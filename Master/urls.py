from django.urls import path
from .views import *

urlpatterns = [
    # Status URLs
    path('status/', status_list, name='status_list'),
    path('status/create/', status_create, name='status_create'),
    path('status/update/<int:pk>/', status_update, name='status_update'),
    path('status/delete/<int:pk>/', status_delete, name='status_delete'),

    # CertificationStatus URLs
    path('certification_status/', certification_status_list, name='certification_status_list'),
    path('certification_status/create/', certification_status_create, name='certification_status_create'),
    path('certification_status/update/<int:pk>/', certification_status_update, name='certification_status_update'),
    path('certification_status/delete/<int:pk>/', certification_status_delete, name='certification_status_delete'),

 # Certification URLs
    path('certification/', certification_list, name='certification_list'),
    path('certification/create/', certification_create, name='certification_create'),
    path('certification/update/<int:pk>/', certification_update, name='certification_update'),
    path('certification/delete/<int:pk>/', certification_delete, name='certification_delete'),

    # Country URLs
    path('country/', country_list, name='country_list'),
    path('country_create/', country_create, name='country_create'),
    path('country_update/<int:pk>/', country_update, name='country_update'),
    path('country_delete/<int:pk>/', country_delete, name='country_delete'),

    # State URLs
    path('state/', state_list, name='state_list'),
    path('state/create/', state_create, name='state_create'),
    path('state/update/<int:pk>/', state_update, name='state_update'),
    path('state/delete/<int:pk>/', state_delete, name='state_delete'),

    # City URLs
    path('city/', city_list, name='city_list'),
    path('city/create/', city_create, name='city_create'),
    path('city/update/<int:pk>/', city_update, name='city_update'),
    path('city/delete/<int:pk>/', city_delete, name='city_delete'),

    # Product Category
    path('product-categories/', product_category_list, name='product_category_list'),
    path('product-categories/create/', product_category_create, name='product_category_create'),
    path('product-categories/update/<int:pk>/', product_category_update, name='product_category_update'),
    path('product-categories/delete/<int:pk>/', product_category_delete, name='product_category_delete'),

    # Schedule Types
    path('schedule-types/', schedule_types_list, name='schedule_types_list'),
    path('schedule-types/create/', schedule_types_create, name='schedule_types_create'),
    path('schedule-types/update/<int:pk>/', schedule_types_update, name='schedule_types_update'),
    path('schedule-types/delete/<int:pk>/', schedule_types_delete, name='schedule_types_delete'),

    # News Category
    path('news-categories/', news_category_list, name='news_category_list'),
    path('news-categories/create/', news_category_create, name='news_category_create'),
    path('news-categories/update/<int:pk>/', news_category_update, name='news_category_update'),
    path('news-categories/delete/<int:pk>/', news_category_delete, name='news_category_delete'),


]
