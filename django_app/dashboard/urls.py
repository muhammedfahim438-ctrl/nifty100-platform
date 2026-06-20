"""
dashboard/urls.py — all public website URL routes
Included from core/urls.py at the root path: path('', include('dashboard.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.home,           name='home'),
    path('companies/',                views.company_list,   name='company_list'),
    path('company/<str:symbol>/',     views.company_detail, name='company_detail'),
    path('search/',                   views.company_search, name='company_search'),
    path('screener/',                 views.screener,       name='screener'),
    path('compare/',                  views.compare,        name='compare'),
    path('sectors/',                  views.sector_list,    name='sector_list'),
    path('sector/<str:name>/',        views.sector_detail,  name='sector_detail'),
    path('health-scores/',            views.health_scores,  name='health_scores'),
]