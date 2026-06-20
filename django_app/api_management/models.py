"""
api_management/models.py
Models for Channel Partner API key management, rate limiting, webhooks.
"""
import uuid
import hashlib
import secrets
# pyrefly: ignore [missing-import]
import bcrypt
from django.db import models
from django.utils import timezone


class ChannelPartner(models.Model):
    """A registered company/developer that has API access."""

    TIER_CHOICES = [
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=200)
    contact_email = models.EmailField(unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='BASIC')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'channel_partners'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} ({self.tier})"


class APIKey(models.Model):
    """HMAC API key pair for a channel partner. Secret stored as bcrypt hash."""

    partner = models.ForeignKey(
        ChannelPartner, on_delete=models.CASCADE, related_name='api_keys'
    )
    key_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    key_secret_hash = models.CharField(max_length=255)
    label = models.CharField(max_length=100, default='Default Key')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.partner.company_name} — {self.key_id}"

    @classmethod
    def create_key_pair(cls, partner, label='Default Key'):
        raw_secret = secrets.token_hex(32)
        hashed = bcrypt.hashpw(raw_secret.encode(), bcrypt.gensalt()).decode()
        key = cls.objects.create(
            partner=partner,
            key_secret_hash=hashed,
            label=label,
        )
        return key, raw_secret

    def verify_secret(self, raw_secret: str) -> bool:
        try:
            return bcrypt.checkpw(raw_secret.encode(), self.key_secret_hash.encode())
        except Exception:
            return False

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at


class APIUsageLog(models.Model):
    """Every request to the partner API is logged here (async via Celery)."""

    api_key = models.ForeignKey(
        APIKey, on_delete=models.SET_NULL, null=True, related_name='usage_logs'
    )
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True)
    request_size_bytes = models.IntegerField(default=0)
    response_size_bytes = models.IntegerField(default=0)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_usage_logs'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['api_key', 'requested_at']),
            models.Index(fields=['endpoint', 'requested_at']),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} → {self.status_code}"


class WebhookEndpoint(models.Model):
    """A URL registered by a partner to receive event notifications."""

    EVENT_CHOICES = [
        ('score_updated', 'Health Score Updated (>2 point change)'),
        ('anomaly_flagged', 'Anomaly Flagged by ML Engine'),
    ]

    partner = models.ForeignKey(
        ChannelPartner, on_delete=models.CASCADE, related_name='webhook_endpoints'
    )
    url = models.URLField(max_length=500)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_endpoints'

    def __str__(self):
        return f"{self.partner.company_name} → {self.event_type} @ {self.url[:50]}"


class WebhookEvent(models.Model):
    """Delivery log for every webhook dispatch attempt."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('RETRYING', 'Retrying'),
    ]

    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name='events'
    )
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} → {self.status} (attempt {self.attempt_count})"