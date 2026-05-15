"""
URL routing for the Nifty 100 API.
"""

from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views

urlpatterns = [
    # Company endpoints
    path("companies/",                          views.CompanyListView.as_view(),       name="company-list"),
    path("companies/<str:symbol>/",             views.CompanyDetailView.as_view(),     name="company-detail"),
    path("companies/<str:symbol>/financials/",  views.CompanyFinancialsView.as_view(), name="company-financials"),

    # Sector endpoints
    path("sectors/",                            views.SectorListView.as_view(),        name="sector-list"),

    # Health scores
    path("scores/",                             views.HealthScoreListView.as_view(),   name="health-scores"),

    # Screener
    path("screener/",                           views.screener_view,                   name="screener"),

    # API Documentation
    path("schema/",                             SpectacularAPIView.as_view(),          name="schema"),
    path("docs/",                               SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]