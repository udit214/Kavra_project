from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('' , views.LandingPage , name='LandingPage'),
    path('collections', views.Collections , name='collections'),
    path('ourstory' , views.OurStory , name='ourstory'),
    path('all_products-<str:allproducts>' , views.AllProducts),
    path('productDetail-<str:product>' , views.ProductPage ),
    path('cart' , views.CartPage , name='cart_page'),
    path('cart/add/<int:variant_id>/', views.AddToCart, name='add_to_cart'),
    path('cart/increase/<int:variant_id>/', views.IncreaseQty, name='increase_qty'),
    path('cart/decrease/<int:variant_id>/', views.DecreaseQty, name='decrease_qty'),
    path('cart/remove/<int:variant_id>/', views.RemoveFromCart, name='remove_from_cart'),
    path('checkout/', views.Checkout, name='checkout'),
    path('lookbook' , views.lookbook , name='lookbook'),
    path('adminside' , views.adminlogin , name='adminlogin')
]
