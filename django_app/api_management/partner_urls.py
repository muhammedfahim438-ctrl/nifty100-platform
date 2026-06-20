"""
api_management/partner_urls.py
Channel Partner REST API — all authenticated endpoints for paying partners.
Mounted at: /api/partner/v1/
"""
from django.urls import path
from .partner_views import (
    PartnerCompanyFullView,
    PartnerBulkFinancialsView,
    PartnerScreenerView,
    PartnerScoresView,
    PartnerKeyListView,
    PartnerKeyDetailView,
    PartnerWebhookListView,
    PartnerWebhookDetailView,
)

urlpatterns = [
    # Company data
    path('companies/<str:symbol>/full/',  PartnerCompanyFullView.as_view(),    name='partner-company-full'),
    path('bulk-financials/',              PartnerBulkFinancialsView.as_view(), name='partner-bulk-financials'),
    path('screener/',                     PartnerScreenerView.as_view(),        name='partner-screener'),
    path('scores/',                       PartnerScoresView.as_view(),          name='partner-scores'),

    # API Key management
    path('keys/',                         PartnerKeyListView.as_view(),         name='partner-keys-list'),
    path('keys/<uuid:key_id>/',           PartnerKeyDetailView.as_view(),       name='partner-keys-detail'),

    # Webhook management
    path('webhooks/',                     PartnerWebhookListView.as_view(),     name='partner-webhooks-list'),
    path('webhooks/<int:pk>/',            PartnerWebhookDetailView.as_view(),   name='partner-webhooks-detail'),
]
