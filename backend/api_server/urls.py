"""URL configuration for api_server project."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('apps.user.urls')),
    path('device/', include('apps.device.urls')),
    path('receive_log/', include('apps.receive_log.urls')),
    path('email/', include('apps.email.urls')),
]
