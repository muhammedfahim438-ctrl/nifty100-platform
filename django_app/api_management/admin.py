"""
api_management/admin.py
Registers ChannelPartner, APIKey, APIUsageLog, WebhookEndpoint, WebhookEvent
in Django's built-in admin (/django-admin/) for manual management and debugging.
The custom /admin-insights/ dashboard (built later) provides the polished,
business-facing version of this same data.
"""
from django.contrib import admin
from .models import ChannelPartner, APIKey, APIUsageLog, WebhookEndpoint, WebhookEvent


@admin.register(ChannelPartner)
class ChannelPartnerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_email', 'tier', 'is_active', 'created_at']
    list_filter = ['tier', 'is_active']
    search_fields = ['company_name', 'contact_email']
    readonly_fields = ['id', 'created_at']


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['key_id', 'partner', 'label', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active']
    search_fields = ['partner__company_name', 'label']
    readonly_fields = ['key_id', 'key_secret_hash', 'created_at', 'last_used_at']

    def has_add_permission(self, request):
        # Keys must be created via the API (create_key_pair) so the raw
        # secret can be shown once — not through the admin form.
        return False


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'method', 'status_code', 'response_time_ms', 'api_key', 'requested_at']
    list_filter = ['method', 'status_code']
    search_fields = ['endpoint']
    readonly_fields = [f.name for f in APIUsageLog._meta.fields]

    def has_add_permission(self, request):
        return False  # logs are written only by Celery tasks


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['partner', 'event_type', 'url', 'is_active', 'created_at']
    list_filter = ['event_type', 'is_active']
    search_fields = ['partner__company_name', 'url']
    readonly_fields = ['secret', 'created_at']


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'endpoint', 'status', 'attempt_count', 'response_status_code', 'created_at']
    list_filter = ['status', 'event_type']
    readonly_fields = [f.name for f in WebhookEvent._meta.fields]

    def has_add_permission(self, request):
        return False  # events are created by fire_webhook_event task