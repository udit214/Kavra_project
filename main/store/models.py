from django.db import models
import uuid
# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from django_resized import ResizedImageField
from django.db.models import Sum
import random
import string
from django.utils.text import slugify
def generate_unique_sku():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        sku = f"KAV-{code}"
        if not Product.objects.filter(sku_base=sku).exists():
            return sku


class Collection(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = ResizedImageField(
        size=[1200, 1500],           # Max width/height (Perfect for vertical luxury shots)
        crop=['middle', 'center'],   # Auto-crop to fill the dimensions
        quality=85,                  # High-quality compression
        upload_to='collections/%Y/', 
        force_format='JPEG',         # Convert PNGs to JPEGs for smaller file sizes
        blank=True, 
        null=True
    )
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Collection, self).save(*args, **kwargs)
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

class Product(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    sku_base = models.CharField(max_length=50, unique=True, verbose_name="Base SKU")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sku_base:
            self.sku_base = generate_unique_sku()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    stock_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    
    @property
    def sku_full(self):
        return f"{self.product.sku_base}-{self.size}"

class Order(models.Model):
    PAYMENT_METHODS = [('CARD', 'Credit Card'), ('COD', 'Cash on Delivery')]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('PAID', 'Processing/Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Your original fields
    order_id = models.CharField(max_length=20, unique=True, editable=False ,default="")
    customer_email = models.EmailField(default="")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2 , default="")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS , default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW: Added shipping fields to make the model functional for checkout
    full_name = models.CharField(max_length=100 , default="")
    phone = models.CharField(max_length=20, default="")
    address = models.TextField(default="")
    city = models.CharField(max_length=50 , default="")
    postal_code = models.CharField(max_length=20 , default="")

    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generates a unique ID like KAV-7A2B
            self.order_id = f"KAV-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.full_name}"

class OrderItem(models.Model):
    # This links the products to the order
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of purchase
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name}"
    
class LandingPageConfig(models.Model):
    heading1_word1 = models.CharField(max_length=9, blank=True, null=True)
    heading1_word2 = models.CharField(max_length=9, blank=True, null=True)
    subheading1 = models.CharField(max_length=40, blank=True, null=True)
    subheading2 = models.CharField(max_length=20, blank=True, null=True)
    # Update this line specifically:
    heading2 = models.CharField(max_length=20, blank=True, null=True) 
    button1_text = models.CharField(max_length=20, blank=True, null=True)
    button2_text = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "Landing Page Configuration"
        verbose_name_plural = "Landing Page Configuration"

    def save(self, *args, **kwargs):
        # Always save to the same row
        self.id = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        # Helper to get the config or create a blank one if it doesn't exist
        obj, created = cls.objects.get_or_create(id=1)
        return obj
    

class OurStoryConfig(models.Model):
    subheading1 = models.CharField(max_length=20 , blank=True , null=True)
    heading1 = models.CharField(max_length=15 , blank=True , null=True)
    subheading2 = models.CharField(max_length=20 , blank=True , null=True)
    paragraph1 = models.CharField(max_length=100 , blank=True , null=True)
    heading2_word1 = models.CharField(max_length=10 , blank=True , null=True)
    heading2_word2 = models.CharField(max_length=10 , blank=True , null=True)
    paragraph2 = models.CharField(max_length=100 , blank=True , null=True)
    paragraph3 = models.CharField(max_length=100 , blank=True , null=True)
    heading3 = models.CharField(max_length=20,blank=True , null=  True)
    subheading3 = models.CharField(max_length=100,blank=True , null=  True)
    subheading4 = models.CharField(max_length=100 , blank=True , null=  True)
    heading4 = models.CharField(max_length=25 , blank=True , null=  True)


    class Meta:
        verbose_name = "our story Page Configuration"
        verbose_name_plural = "our story Page Configuration"

    def save(self, *args, **kwargs):
        # Always save to the same row
        self.id = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        # Helper to get the config or create a blank one if it doesn't exist
        obj, created = cls.objects.get_or_create(id=1)
        return obj
    

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_spent(self):
        # Calculates sum from the Order model related to this customer
        return self.orders.filter(status='DELIVERED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    @property
    def order_count(self):
        return self.orders.count()

    @property
    def is_vip(self):
        return self.total_spent > 2000  # Threshold for VIP status
    
class SiteSettings(models.Model):
    store_name = models.CharField(max_length=100, default="KAVRA Luxury Apparel")
    support_email = models.EmailField(default="concierge@kavra.com")
    maintenance_mode = models.BooleanField(default=False)
    cod_enabled = models.BooleanField(default=True)
    international_shipping = models.BooleanField(default=True)
    announcement_banner = models.CharField(max_length=255, default="Complimentary Express Shipping.")

    class Meta:
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Global Site Settings"