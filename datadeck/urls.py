"""
URL configuration for datadeck project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from video_app.auth_views import AdminLoginView
from django.contrib.auth import views as auth_views
from video_app.media_views import upload_media

urlpatterns = [
    # Admin authentication first
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='home'), name='admin_logout'),
    
    # Your app's URLs before Django admin
    path('', include('video_app.urls')),
    
    # Django admin last
    path('admin/', admin.site.urls),
    
    # Other URLs
    path('upload/', upload_media, name='upload_media'),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
