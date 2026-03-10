from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views as dash_views

urlpatterns = [
    # The default Django admin (hidden at a unique path for security)
    path('kavra-system-admin/', admin.site.urls),

    # Authentication (Management Portal)
    path('management/login/', dash_views.admin_login, name='admin_login'),
    path('management/logout/', dash_views.admin_logout, name='admin_logout'),

    # Dashboard App Logic
    path('management/dashboard/', include('dashboard.urls')),

    # Public Store Front
    path('', include('store.urls')),
]

# Media and Static handling for Local Development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)