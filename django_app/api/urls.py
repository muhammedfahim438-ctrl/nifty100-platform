"""
api/urls.py — Public REST API routes
Included from core/urls.py at: path('api/v1/', include('api.urls'))
"""
from django.urls import path
from .views import (
    CompanyListView, CompanyDetailView, CompanyFinancialsView,
    SectorListView, ScoresListView, ScreenerView,
)

urlpatterns = [
    path('companies/',                       CompanyListView.as_view(),        name='api-company-list'),
    path('companies/<str:symbol>/',          CompanyDetailView.as_view(),      name='api-company-detail'),
    path('companies/<str:symbol>/financials/', CompanyFinancialsView.as_view(), name='api-company-financials'),
    path('sectors/',                         SectorListView.as_view(),         name='api-sector-list'),
    path('scores/',                          ScoresListView.as_view(),         name='api-scores'),
    path('screener/',                        ScreenerView.as_view(),           name='api-screener'),
]