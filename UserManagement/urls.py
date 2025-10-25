from django.urls import path
from .views import *

urlpatterns = [
    path('log/', login, name='login'),
    path('signup/', customer_signup, name='customer_signup'),
    path('admin_signup/', admin_signup, name='admin_signup'),
    path('admin_list/', admin_list, name='admin_list'),
    path('user_list/', user_list, name='user_list'),

    path('', index, name='index'),
    path('admin_dash/', admin_dash, name='admin_dash'),
    path('user_dash/', user_dash, name='user_dash'),
    # path('user_dash/', user_dashboard, name='user_dash'),

    path('table/',table,name='table'),


    path('pending_users/',pending_users,name='user_pending_list'),
    path('user_pending_view/<int:pk>/',user_pending_view,name='user_pending_view'),
    path('approve_user/<int:temp_user_id>/',approve_user,name='approve_user'),
    

    path('point_allocations/', point_allocation_list, name='point_allocation_list'),
    path('point_allocations_user/', point_allocation_list_user, name='point_allocation_list_user'),
    path('point_allocations/create/', point_allocation_create, name='point_allocation_create'),
    path('point_allocations/update/<int:pk>/', point_allocation_update, name='point_allocation_update'),
    path('point_allocations/delete/<int:pk>/', point_allocation_delete, name='point_allocation_delete'),
    path('logout_view/', logout_view, name='logout_view'),
]
