from django.contrib import admin

# Register your models here.
from . models import *

admin.site.register(Collection)
admin.site.register(Order)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(OrderItem)
admin.site.register(LandingPageConfig)
admin.site.register(OurStoryConfig)
