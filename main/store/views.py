from django.shortcuts import render
from . models import Product

# Create your views here.
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductVariant, Order , Collection , Product,Order, OrderItem,LandingPageConfig,OurStoryConfig
import uuid
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from .models import ProductVariant
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from dashboard.models import GenralSettings


def LandingPage(request):
    genral_settings = GenralSettings.objects.get(id=1)
    print(genral_settings.Store_name)
    content = LandingPageConfig.load()
    print(content.heading1_word1 , '___________________')
    collections = Collection.objects.all().order_by('-id')[:3]
    return render(request , 'index.html' , {'collections' : collections , 'content':content ,'genral_settings':genral_settings})

def Collections(request):
    collections = Collection.objects.all()
    return render(request , 'collections.html', {'collections' : collections})

def OurStory(request):
    content = OurStoryConfig.load()
    return render(request , 'outstory.html' ,{'content':content})

def AllProducts(request, allproducts):
    # 1. Initial Filtering by Collection
    if allproducts == 'all_products':
        products = Product.objects.all()
    else:
        collection = get_object_or_404(Collection, slug=allproducts)
        products = Product.objects.filter(collection=collection)

    # 2. Filter by Size (Many-to-Many / Variant check)
    size_filter = request.GET.get('size')
    if size_filter:
        # We filter products that have a variant with this size and stock > 0
        products = products.filter(variants__size=size_filter, variants__stock_quantity__gt=0).distinct()

    # 3. Sorting Logic
    sort_by = request.GET.get('sort')
    if sort_by == 'price-low':
        products = products.order_by('price')
    elif sort_by == 'price-high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-id') # Assuming higher ID = newer

    # Get all collections for the sidebar links
    all_collections = Collection.objects.all()
    
    context = {
        'products': products,
        'all_collections': all_collections,
        'current_slug': allproducts,
        'current_size': size_filter,
        'current_sort': sort_by
    }
    return render(request, 'allproduct.html', context)

def ProductPage(request , product):

    the_product = Product.objects.get(sku_base = product)
    print(the_product.price)
    
    return render(request, 'productDetail.html', {'product':the_product})

def CartPage(request):
    cart = request.session.get('cart', {}) # Ensure this matches AddToCart
    bag_items = []
    total_price = 0

    for variant_id, quantity in cart.items():
        try:
            # We get the Variant (which contains the Size and a link to the Product)
            variant = ProductVariant.objects.get(id=variant_id)
            
            # Use the price from the parent Product
            line_total = variant.product.price * quantity
            total_price += line_total
            
            bag_items.append({
                'variant': variant, 
                'product': variant.product, # Sending the product explicitly makes the HTML cleaner
                'quantity': quantity,
                'line_total': line_total,
            })
        except ProductVariant.DoesNotExist:
            continue

    return render(request, 'cart.html', {
        'bag_items': bag_items, 
        'total_price': total_price
    })

def AddToCart(request, variant_id):
    # 1. Get the bag from the session (default to empty dict)
    cart = request.session.get('cart', {})

    # 2. Check if the item exists in the DB
    variant = get_object_or_404(ProductVariant, id=variant_id)
    
    # 3. Add to cart logic
    variant_id_str = str(variant_id) # Session keys must be strings
    if variant_id_str in cart:
        cart[variant_id_str] += 1
    else:
        cart[variant_id_str] = 1

    # 4. Save back to session
    request.session['cart'] = cart
    request.session.modified = True
    
    # 5. Redirect to the cart page we just built
    return redirect('cart_page')

from django.shortcuts import redirect, get_object_or_404

def IncreaseQty(request, variant_id):
    cart = request.session.get('cart', {})
    variant_id_str = str(variant_id)
    
    if variant_id_str in cart:
        cart[variant_id_str] += 1
        
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_page')

def DecreaseQty(request, variant_id):
    cart = request.session.get('cart', {})
    variant_id_str = str(variant_id)
    
    if variant_id_str in cart:
        if cart[variant_id_str] > 1:
            cart[variant_id_str] -= 1
        else:
            # If quantity is 1 and user clicks minus, remove it
            del cart[variant_id_str]
            
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_page')

def RemoveFromCart(request, variant_id):
    cart = request.session.get('cart', {})
    variant_id_str = str(variant_id)
    
    if variant_id_str in cart:
        del cart[variant_id_str]
        
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_page')

def Checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart_page')

    bag_items = []
    total_price = 0
    for variant_id, quantity in cart.items():
        variant = ProductVariant.objects.get(id=variant_id)
        line_total = variant.product.price * quantity
        total_price += line_total
        bag_items.append({'variant': variant, 'quantity': quantity, 'line_total': line_total})

    if request.method == 'POST':
        # Create Order using your updated model fields
        order = Order.objects.create(
            customer_email=request.POST['email'],
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            city=request.POST['city'],
            postal_code=request.POST['postal_code'],
            total_amount=total_price,
            payment_method=request.POST['payment_method'],
            status='PENDING'
        )

        # Save individual items
        for item in bag_items:
            OrderItem.objects.create(
                order=order,
                product_variant=item['variant'],
                price=item['variant'].product.price,
                quantity=item['quantity']
            )
        # 1. Setup the Subject and Context
        subject = f"Your KAVRA Selection: {order.order_id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = order.customer_email

        # 2. Render the HTML content
        html_content = render_to_string('email.html', {'order': order})
        text_content = strip_tags(html_content) # Create plain-text version for backup

        # 3. Create the email object
        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html") # Attach the high-end version

            # 4. Send
            msg.send(fail_silently=False)
            # Clear the luxury bag
            request.session['cart'] = {}
            request.session.modified = True
        except Exception as e:
            # This logs the error to your server console so you can read it,
            # but it doesn't crash the page for the customer.
            print(f"Email failed to send: {e}")

        return render(request, 'success.html', {'order': order})

    return render(request, 'checkoutpage.html', {'bag_items': bag_items, 'total_price': total_price})

def lookbook(request):
    return render(request , 'lookbook.html')

def adminlogin(request):
    return render(request , 'adminpanel/login.html')