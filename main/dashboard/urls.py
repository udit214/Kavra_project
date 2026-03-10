
from django.urls import path
from . import views

urlpatterns = [
    # This maps to /management/dashboard/
    path('', views.dashboard_home, name='dashboard_home'),
    
    # These map to /management/dashboard/inventory/, etc.
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/add/', views.add_product, name='add_product'),
    path('orders/', views.orders_list, name='orders'),
    path('customers/', views.customer_list, name='customers'),
    path('settings/', views.settings_view, name='settings'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('addproduct/' , views.add_product , name='add_product'),
    path('verify-order/<int:order_id>/' , views.verify_order , name='verify_order'),
    path('inventory/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('inventory/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('collections/', views.manage_collections, name='manage_collections'),
    path('collections/add/', views.add_collection, name='add_collection'),
    path('collections/delete/<int:pk>/', views.delete_collection, name='delete_collection'),
    path('collections/edit/<int:pk>/', views.edit_collection, name='edit_collection'),
    path('order/<int:order_id>/invoice/', views.generate_invoice, name='generate_invoice'),
]