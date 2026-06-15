"""
URL routing for HTML template pages.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("",                      views.home,           name="home"),
    path("companies/",            views.company_list,   name="company-list-html"),
    path("company/<str:symbol>/", views.company_detail, name="company-detail-html"),
    path("compare/",              views.compare,        name="compare"),
    path("screener/",             views.screener,       name="screener-html"),
    path("sector/<str:name>/",    views.sector_detail,  name="sector-detail"),
]