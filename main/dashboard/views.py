from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from store.models import LandingPageConfig # Adjust the import based on where your model lives
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F
import random
import string
from django.db.models import Q, Avg
from store.models import Order, Product, ProductVariant, LandingPageConfig ,Collection,Customer,LandingPageConfig, OurStoryConfig,SiteSettings
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from . models import GenralSettings


# Security Check: Only allow staff/admins
def is_admin(user):
    return user.is_authenticated and user.is_staff

# --- AUTH VIEWS ---

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard_home')
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard_home')
        else:
            messages.error(request, "Access Denied: Invalid Credentials")
    return render(request, 'adminpanel/login.html')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

# --- DASHBOARD VIEWS ---

@user_passes_test(is_admin, login_url='admin_login')
def dashboard_home(request):
    # Aggregating Real Data
    total_sales = Order.objects.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    active_orders = Order.objects.exclude(status__in=['DELIVERED', 'CANCELLED']).count()
    
    # Inventory Alerts: Summing stock across variants where stock is low
    low_stock_threshold = 5
    low_stock_variants = ProductVariant.objects.filter(stock_quantity__lt=low_stock_threshold).select_related('product')
    alert_count = low_stock_variants.count()

    # Recent Transactions
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'total_sales': total_sales,
        'active_orders_count': active_orders,
        'alert_count': alert_count,
        'recent_orders': recent_orders,
        'low_stock_items': low_stock_variants,
    }
    return render(request, 'adminpanel/adminpanel.html', context)

@user_passes_test(is_admin, login_url='admin_login')
def settings_view(request):
    # Load all singletons
    site_config, created = GenralSettings.objects.get_or_create(id=1)
    site_cfg = SiteSettings.objects.get_or_create(id=1)[0]
    landing_cfg = LandingPageConfig.load()
    story_cfg = OurStoryConfig.load()

    if request.method == "POST":
        form_type = request.POST.get('form_type')

        if form_type == "general":

            site_config.Store_name = request.POST.get('store_name')
            site_config.Site_email = request.POST.get('support_email')
            site_config.maintenance_mode = 'maintenance' in request.POST
            site_config.cod_enabled = 'cod' in request.POST
            site_config.Instagram = request.POST.get('instagram')       
            site_config.contact = request.POST.get('contact')           
            site_config.Email_app_code = request.POST.get('email_code') 
            site_config.save()

        if form_type == "landing":
            landing_cfg.heading1_word1 = request.POST.get('h1_w1')
            landing_cfg.heading1_word2 = request.POST.get('h1_w2')
            landing_cfg.subheading1 = request.POST.get('sub1')
            landing_cfg.subheading2 = request.POST.get('sub2')
            landing_cfg.heading2 = request.POST.get('h2')
            landing_cfg.button1_text = request.POST.get('btn1')
            landing_cfg.button2_text = request.POST.get('btn2')
            landing_cfg.save()
            
        elif form_type == "story":
            story_cfg.heading1 = request.POST.get('s_h1')
            story_cfg.subheading1 = request.POST.get('s_sub1')
            story_cfg.paragraph1 = request.POST.get('s_p1')
            story_cfg.heading2_word1 = request.POST.get('s_h2_w1')
            story_cfg.heading2_word2 = request.POST.get('s_h2_w2')
            story_cfg.paragraph2 = request.POST.get('s_p2')
            story_cfg.heading3 = request.POST.get('s_h3')
            story_cfg.save()

        messages.success(request, f"{form_type.capitalize()} settings updated.")
        return redirect('settings')

    return render(request, 'adminpanel/settings.html', {
        'site': site_config,
        'landing': landing_cfg,
        'story': story_cfg
    })

# --- STUBS FOR OTHER PAGES ---
@user_passes_test(is_admin, login_url='admin_login')
def inventory_view(request):
    query = request.GET.get('search', '')
    stock_filter = request.GET.get('filter', '')
    
    # 1. Base Query with optimized related lookups
    products = Product.objects.select_related('collection').prefetch_related('variants').all().order_by('-id')

    # 2. Search Logic
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku_base__icontains=query)
        )

    # 3. Process Products to attach stock attributes manually
    for p in products:
        # Get variants for this product
        variants = p.variants.all()
        
        # Map stock quantities to the attributes the template expects
        p.stock_s = next((v.stock_quantity for v in variants if v.size == 'S'), 0)
        p.stock_m = next((v.stock_quantity for v in variants if v.size == 'M'), 0)
        p.stock_l = next((v.stock_quantity for v in variants if v.size == 'L'), 0)
        p.stock_xl = next((v.stock_quantity for v in variants if v.size == 'XL'), 0)
        
        p.total_stock = p.stock_s + p.stock_m + p.stock_l + p.stock_xl

    # 4. Low Stock Filter Logic (Post-processing)
    if stock_filter == 'low_stock':
        products = [p for p in products if p.total_stock < 15]

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'adminpanel/inventory.html', context)
@user_passes_test(is_admin, login_url='admin_login')

def delete_product(request, pk):
    if request.method == "POST":
        product = get_object_or_404(Product, pk=pk)
        product.delete() # This deletes the variants too!
        messages.success(request, "Product and its variants removed.")
    return redirect('inventory')


def add_product(request):
    size_data = [('S', 'Small'), ('M', 'Medium'), ('L', 'Large'), ('XL', 'Extra Large')]

    if request.method == "POST":
        try:
            with transaction.atomic():

                # Get collection
                col_id = request.POST.get('collection')
                col = get_object_or_404(Collection, id=col_id)

                # Create product (SKU will auto generate in model.save())
                product = Product.objects.create(
                    collection=col,
                    name=request.POST.get('name'),
                    description=request.POST.get('description'),
                    price=request.POST.get('price'),
                    image=request.FILES.get('product_image')
                )

                # Create variants
                for code, _ in size_data:
                    qty = request.POST.get(f'qty_{code}', 0)

                    ProductVariant.objects.create(
                        product=product,
                        size=code,
                        stock_quantity=int(qty) if qty else 0
                    )

                messages.success(
                    request,
                    f"Product '{product.name}' created successfully with SKU {product.sku_base}"
                )

                return redirect('inventory')

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            messages.error(request, f"Error creating product: {e}")

    return render(request, 'adminpanel/addproduct.html', {
        'collections': Collection.objects.all(),
        'sizes': size_data
    })
@user_passes_test(is_admin, login_url='admin_login')
def orders_list(request):
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        orders = Order.objects.filter(status='PENDING')
    elif status_filter == 'toship':
        orders = Order.objects.filter(status='TOSHIP')
    elif status_filter == 'completed':
        orders = Order.objects.filter(status='DELIVERED')
    else:
        orders = Order.objects.all().order_by('-created_at')

    return render(request, 'adminpanel/orders.html', {
        'orders': orders,
        'current_status': status_filter
    })

def verify_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'TOSHIP'
    order.save()
    return redirect('orders')

@user_passes_test(is_admin, login_url='admin_login')
def customer_list(request):
    query = request.GET.get('search', '')
    
    if query:
        customers = Customer.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        )
    else:
        customers = Customer.objects.all().order_by('-last_active')

    # Stats for the cards
    total_clients = Customer.objects.count()
    # Filter for VIPs (those who spent > 2000)
    vip_count = sum(1 for c in customers if c.is_vip)
    avg_order = Order.objects.aggregate(Avg('total_amount'))['total_amount__avg'] or 0

    context = {
        'customers': customers,
        'total_clients': total_clients,
        'vip_count': vip_count,
        'avg_order': avg_order,
        'query': query
    }
    return render(request, 'adminpanel/customers.html', context)

@user_passes_test(is_admin, login_url='admin_login')
def analytics_view(request):
    return render(request, 'adminpanel/anylytics.html')

def add_product(request):
    collections = Collection.objects.all()
    
    if request.method == "POST":
        # 1. Get General Info
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        sku_base = request.POST.get('sku_base')
        collection_id = request.POST.get('collection')
        image = request.FILES.get('product_image')

        # 2. Create the Product
        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            sku_base=sku_base,
            collection_id=collection_id,
            image=image
        )

        # 3. Create Variants (S, M, L, XL)
        sizes = ['S', 'M', 'L', 'XL']
        for size in sizes:
            qty = request.POST.get(f'qty_{size}', 0)
            if qty:
                ProductVariant.objects.create(
                    product=product,
                    size=size,
                    stock_quantity=qty
                )

        messages.success(request, f"Luxury Piece '{name}' published successfully.")
        return redirect('inventory')

    return render(request, 'adminpanel/addproduct.html', {'collections': collections})

@user_passes_test(is_admin, login_url='admin_login')

def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    collections = Collection.objects.all()

    # GET: Prepare the current stock levels to show in the form
    variants = product.variants.all()
    stock_data = {
        'stock_s': next((v.stock_quantity for v in variants if v.size == 'S'), 0),
        'stock_m': next((v.stock_quantity for v in variants if v.size == 'M'), 0),
        'stock_l': next((v.stock_quantity for v in variants if v.size == 'L'), 0),
        'stock_xl': next((v.stock_quantity for v in variants if v.size == 'XL'), 0),
    }

    if request.method == "POST":
        # 1. Update core product info
        product.name = request.POST.get('name')
        product.sku_base = request.POST.get('sku')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        
        col_id = request.POST.get('collection')
        if col_id:
            product.collection = get_object_or_404(Collection, id=col_id)
            
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()

        # 2. Update the actual Variant records (This makes it reflect in inventory)
        size_mapping = {
            'S': request.POST.get('stock_s', 0),
            'M': request.POST.get('stock_m', 0),
            'L': request.POST.get('stock_l', 0),
            'XL': request.POST.get('stock_xl', 0),
        }

        for size_code, quantity in size_mapping.items():
            ProductVariant.objects.update_or_create(
                product=product, 
                size=size_code,
                defaults={'stock_quantity': quantity if quantity else 0}
            )

        messages.success(request, f"Piece '{product.name}' updated successfully.")
        return redirect('inventory')

    # Add collections and current stock to context
    context = {
        'product': product, 
        'collections': collections,
        **stock_data 
    }
    return render(request, 'adminpanel/edit_product.html', context)

def analytics_view(request):
    # 1. Calculate Date Ranges
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    prev_month_start = today - timedelta(days=60)
    
    # 2. Key Metrics
    total_sales = Order.objects.filter(created_at__gte=last_30_days).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    prev_sales = Order.objects.filter(created_at__range=[prev_month_start, last_30_days]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate Growth %
    growth = 0
    if prev_sales > 0:
        growth = ((total_sales - prev_sales) / prev_sales) * 100

    # 3. Line Chart Data (Last 5 weeks)
    revenue_labels = []
    revenue_data = []
    for i in range(4, -1, -1):
        date = today - timedelta(weeks=i)
        revenue_labels.append(date.strftime('%b %d'))
        sum_val = Order.objects.filter(created_at__week=date.isocalendar()[1]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        revenue_data.append(float(sum_val))

    # 4. Payment Method Ratio
    prepaid_count = Order.objects.filter(created_at__gte=last_30_days, payment_method='Prepaid').count()
    cod_count = Order.objects.filter(created_at__gte=last_30_days, payment_method='COD').count()
    total_orders = prepaid_count + cod_count
    
    prepaid_pct = round((prepaid_count / total_orders * 100), 1) if total_orders > 0 else 0
    cod_pct = 100 - prepaid_pct if total_orders > 0 else 0

    # 5. Best Sellers (Joining Orders/OrderItems or using a 'sales_count' field)
    # Assuming Product has a sales_count field, or replace with OrderItem aggregation
    best_sellers = Product.objects.all().order_by('-id')[:4] # Placeholder: Replace with actual sales logic

    context = {
        'total_sales': total_sales,
        'growth': round(growth, 1),
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'prepaid_pct': prepaid_pct,
        'cod_pct': cod_pct,
        'best_sellers': best_sellers,
    }
    return render(request, 'adminpanel/analytics.html', context)


def manage_collections(request):
    collections = Collection.objects.all().order_by('-id')
    return render(request, 'adminpanel/manage_collections.html', {'collections': collections})

def add_collection(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        Collection.objects.create(
            name=name,
            description=description,
            image=image
        )
        messages.success(request, f"Collection '{name}' created successfully!")
        return redirect('manage_collections')

    return render(request, 'adminpanel/add_collection.html')

def delete_collection(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    collection.delete()
    messages.success(request, "Collection deleted.")
    return redirect('manage_collections')

def edit_collection(request, pk):
    # Fetch the existing collection or return 404
    collection = get_object_or_404(Collection, pk=pk)

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        new_image = request.FILES.get('image')

        # Update fields
        collection.name = name
        collection.description = description
        
        # Only update image if a new one was uploaded
        if new_image:
            collection.image = new_image
        
        collection.save() # This will also trigger the slug update if name changed
        messages.success(request, f"Collection '{name}' updated successfully.")
        return redirect('manage_collections')

    return render(request, 'adminpanel/edit_collection.html', {'collection': collection})

def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # If you have an OrderItem related model, it will be fetched here
    # order_items = order.items.all() 
    
    return render(request, 'adminpanel/invoice_print.html', {
        'order': order,
        # 'items': order_items,
    })