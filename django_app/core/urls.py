"""
Root URL routing for the B100 Intelligence Platform.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/",    admin.site.urls),
    path("",          include("companies.urls")),   # HTML template pages
    path("api/v1/",   include("api.urls")),         # REST API
]