"""
Main URL configuration for Nifty 100 Platform.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/",      admin.site.urls),
    path("api/v1/",     include("api.urls")),
]