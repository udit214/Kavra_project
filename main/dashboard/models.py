from django.db import models

# Create your models here.
class GenralSettings(models.Model):
    Store_name = models.CharField(max_length=30 , blank=True , null=True)
    Site_email = models.EmailField(blank=True , null=True)
    Email_app_code = models.CharField(max_length=20,blank=True , null=True)
    Instagram = models.CharField(max_length=100,blank=True , null=True)
    contact = models.EmailField(blank=True , null=True)