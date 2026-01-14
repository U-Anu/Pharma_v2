from django.urls import path
from django.conf.urls.static import static
from Pharmacy_ECW import settings
from .views import *
urlpatterns = [

    path('compositions/', composition_list, name='composition_list'),
    path('compositions/create/', composition_create, name='composition_create'),
    path('compositions/update/<int:pk>/', composition_update, name='composition_update'),
    path('compositions/delete/<int:pk>/', composition_delete, name='composition_delete'),

    path('upload_composition_from_excel/', upload_composition_from_excel, name='upload_composition_from_excel'),
    path('upload_compositions/', upload_compositions, name='upload_compositions'),

    path('product-types/', product_type_list, name='product_type_list'),
    path('product-types/create/', product_type_create, name='product_type_create'),
    path('product-types/update/<int:pk>/', product_type_update, name='product_type_update'),
    path('product-types/delete/<int:pk>/', product_type_delete, name='product_type_delete'),

    path('products/', product_list, name='product_list'),
    # path('products/', user_product_list, name='product_list'),
    # path('products1/', product_list1, name='product_list1'),
    # path('user_products/', user_product_list, name='user_product_list'),
    path('admin_products/', admin_product_list, name='admin_product_list'),

    path('products/create/', product_create, name='product_create'),
    path('products/update/<int:pk>/', product_update, name='product_update'),
    path('products/delete/<int:pk>/', product_delete, name='product_delete'),
    path('upload/', upload_products, name='upload_products'),

    path("query_list/", query_list, name="query_list"),
    path("query_create/", query_create, name="query_create"),
    path("query_delete/<pk>", query_delete, name="query_delete"),
    path("query_update/<pk>", query_update, name="query_update"),
 
    path('extract_columns/', extract_columns, name='extract_columns'),
    path('delete-all-products/', delete_all_products, name='delete_all_products'),
    path('update-all-products/', update_all_products, name='update_all_products'),

    path('delll/', delll, name='delll'),
    path('delll11/', delll11, name='delll'),

    path('user-categories/', user_category_list, name='user_category_list'),
    path('user-categories/create/', user_category_create, name='user_category_create'),
    path('user-categories/<int:pk>/edit/', user_category_update, name='user_category_update'),
    path('user-categories/<int:pk>/delete/', user_category_delete, name='user_category_delete'),

    path('user-category/<int:category_id>/markups/create/', user_category_markup_create_or_update, name='user_category_markup_create_or_update'),
    path('user-category-markups/', user_category_markup_list, name='user_category_markup_list'),
    path('user-category-markups/<int:category_id>/', user_category_markup_detail, name='user_category_markup_detail'),
    path('user-category-markup/<int:pk>/edit/', user_category_markup_edit, name='user_category_markup_edit'),
    path('user-category-markup/<int:pk>/delete/', user_category_markup_delete, name='user_category_markup_delete'),
    path("products/<int:product_id>/markups/",product_markups, name="product_markups"),
    path('user-category/<int:pk>/margin/create/', user_category_margin_create_or_update, name='user_category_margin_create_or_update'),

]


