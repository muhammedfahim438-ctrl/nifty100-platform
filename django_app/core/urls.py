"""
B100 Intelligence — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django built-in admin
    path('django-admin/', admin.site.urls),

    # Public website pages (Django templates)
    path('', include('dashboard.urls')),

    # Public REST API v1
    path('api/v1/', include('api.urls')),

    # Channel Partner API (HMAC-authenticated)
    path('api/partner/v1/', include('api_management.partner_urls')),

    # Accounts (login/logout)
    path('accounts/', include('accounts.urls')),

    # Admin Insights Dashboard (staff-only)
    path('admin-insights/', include('admin_insights.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]