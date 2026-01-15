from django.urls import path
from django.conf.urls.static import static

from Pharmacy_ECW import settings
from .views import *
urlpatterns = [
# path("user-orders/", user_order_list, name="user_order_list"),
    path("admin/orders/<int:order_id>/issue/", admin_order_issue, name="admin_order_issue"),
    # path('orders/', user_order_list, name='user_order_list'),
    path('admin_orders/', admin_order_list, name='admin_orders'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path("user-query-list/", user_query_list, name="user_query_list"),
    path('user_products/', user_product_list, name='user_product_list'),
    path("user_query_create/", user_query_create, name="user_query_create"),
    path("user_query_update/<pk>", user_query_update, name="user_query_update"),

    path("checkout_and_query/",checkout_and_query,name="checkout_and_query"),
    path("place_order/",place_order,name="place_order"),
    path('product-order/', product_order, name='product_order'),
    path("place-order/", place_order, name="place-order"),
    path("orders/", order_list, name="order_list"),
    path("delivered/", delivered_list, name="delivered_list"),
    path("recent_order/", recent_order_list, name="recent_order_list"),
    
    path("orders-update/<int:pk>/", order_update, name="order_update"),
    path('place_order/',place_order, name='place_order'),
    path('invoice/<int:order_id>/',invoice, name='invoice'),
    path('orders/<int:pk>/note-slip/', order_note_slip, name='order_note_slip'),
    path('orders/<int:pk>/note-slip/download/', download_note_slip, name='download_note_slip'),


    path('customer_order/', customer_order_list, name='customer_order_list'),
    # path('customer_order/create/', customer_order_create, name='customer_order_create'),
    path('customer_order/update/<int:pk>/', customer_order_update, name='customer_order_update'),
    # path('customer_order/delete/<int:pk>/', customer_order_delete, name='customer_order_delete'),


    path('create/', create_order, name='create_order'),
    path('add-to-temp/', add_to_temp, name='add_to_temp'),
    path('remove-temp-item/', remove_temp_item, name='remove_temp_item'),
    
    path("orders/<int:pk>/invoice/", order_invoice, name="order_invoice"),
    path("admin_orders/<int:pk>/invoice/", admin_order_invoice, name="admin_order_invoice"),



    path('customer_order/', customer_order_list, name='customer_order_list'),
    # path('customer_order/create/', customer_order_create, name='customer_order_create'),
    path('customer_order/update/<int:pk>/', customer_order_update, name='customer_order_update'),
    path('customer_order/delete/<int:pk>/', customer_order_delete, name='customer_order_delete'),


    path('create/', create_order, name='create_order'),
    path('add-to-temp/', add_to_temp, name='add_to_temp'),
    path('remove-temp-item/', remove_temp_item, name='remove_temp_item'),
    
    
     path('ajax/add-to-cart/', ajax_add_to_cart, name='ajax_add_to_cart'),
    path('ajax/update-cart-qty/', ajax_update_cart_qty, name='ajax_update_cart_qty'),
    path('ajax/remove-cart-item/', ajax_remove_cart_item, name='ajax_remove_cart_item'),

    path('ajax/remove-temp-query-item/', ajax_remove_temp_query_item, name='ajax_remove_temp_query_item'),
    path('ajax/update-temp-query-qty/', ajax_update_temp_query_qty, name='ajax_update_temp_query_qty'),
    path('ajax/save-query-header/', ajax_save_query_header, name='ajax_save_query_header'),

]