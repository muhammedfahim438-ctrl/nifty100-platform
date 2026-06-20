"""
api_management/serializers.py
Serializers for the channel partner API management endpoints
(API keys, webhooks, and partner-facing company/score data).
"""
from rest_framework import serializers
from .models import ChannelPartner, APIKey, WebhookEndpoint, WebhookEvent


class ChannelPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelPartner
        fields = ['id', 'company_name', 'contact_email', 'tier', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class APIKeySerializer(serializers.ModelSerializer):
    """
    Used for listing existing keys. Never includes key_secret_hash —
    the raw secret is only ever returned once, at creation time,
    directly from the view (see PartnerKeyListView.post in partner_views.py).
    """
    class Meta:
        model = APIKey
        fields = ['key_id', 'label', 'is_active', 'created_at', 'last_used_at', 'expires_at']
        read_only_fields = fields


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = ['id', 'url', 'event_type', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class WebhookEventSerializer(serializers.ModelSerializer):
    endpoint_url = serializers.CharField(source='endpoint.url', read_only=True)

    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'endpoint_url', 'event_type', 'status', 'attempt_count',
            'max_attempts', 'last_attempt_at', 'next_attempt_at',
            'response_status_code', 'created_at',
        ]
        read_only_fields = fields


# ─── Lightweight serializers reused by partner_views.py for company data ───────

class CompanyFullSerializer(serializers.Serializer):
    """Generic passthrough serializer — partner_views builds the dict manually
    for full control over what's exposed to paying partners."""
    symbol = serializers.CharField()
    name = serializers.CharField()


class BulkFinancialsSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    latest_sales = serializers.FloatField(allow_null=True)
    latest_net_profit = serializers.FloatField(allow_null=True)


class HealthScoreSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    overall_score = serializers.FloatField(allow_null=True)
    health_label = serializers.CharField(allow_null=True)