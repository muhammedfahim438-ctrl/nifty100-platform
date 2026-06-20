"""
api_management/tasks.py
Celery tasks for webhook delivery with exponential backoff retry,
and async API usage logging.
"""
import hashlib
import hmac
import json
import logging
import time

import requests
# pyrefly: ignore [missing-import]
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def fire_webhook_event(self, event_type: str, symbol: str, payload: dict):
    """
    Deliver a webhook event to all subscribed endpoints for this event type.
    Retries up to 5 times with exponential backoff (1, 2, 4, 8, 16 minutes).
    """
    from .models import WebhookEndpoint, WebhookEvent

    endpoints = WebhookEndpoint.objects.filter(
        event_type=event_type,
        is_active=True,
        partner__is_active=True,
    )

    full_payload = {
        'event': event_type,
        'symbol': symbol,
        'timestamp': int(time.time()),
        'data': payload,
    }
    body = json.dumps(full_payload, default=str).encode()

    for endpoint in endpoints:
        event_log, _ = WebhookEvent.objects.get_or_create(
            endpoint=endpoint,
            event_type=event_type,
            payload=full_payload,
            defaults={'status': 'PENDING'},
        )

        # Build HMAC signature so partner can verify authenticity
        signature = hmac.new(
            endpoint.secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        try:
            resp = requests.post(
                endpoint.url,
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'X-Bluestock-Signature': f'sha256={signature}',
                    'X-Event-Type': event_type,
                },
                timeout=10,
            )
            resp.raise_for_status()

            event_log.status = 'SUCCESS'
            event_log.response_status_code = resp.status_code
            event_log.response_body = resp.text[:500]
            event_log.attempt_count += 1
            event_log.last_attempt_at = timezone.now()
            event_log.save()
            logger.info(f"[webhooks] Delivered {event_type} to {endpoint.url} — {resp.status_code}")

        except Exception as exc:
            event_log.status = 'RETRYING'
            event_log.attempt_count += 1
            event_log.last_attempt_at = timezone.now()
            event_log.response_body = str(exc)[:500]
            event_log.save()

            logger.warning(f"[webhooks] Delivery failed to {endpoint.url}: {exc}")

            # Exponential backoff: 1, 2, 4, 8, 16 minutes
            backoff = 60 * (2 ** self.request.retries)
            try:
                raise self.retry(exc=exc, countdown=backoff)
            except self.MaxRetriesExceededError:
                event_log.status = 'FAILED'
                event_log.save()
                logger.error(f"[webhooks] Max retries exceeded for {endpoint.url}")


@shared_task
def log_api_usage(key_id, endpoint, method, status_code, response_time_ms, ip_address,
                  request_size, response_size):
    """
    Asynchronously log every channel partner API request.
    Called as a fire-and-forget task from partner API views.
    """
    from .models import APIKey, APIUsageLog
    try:
        api_key = APIKey.objects.get(key_id=key_id)
        APIUsageLog.objects.create(
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            request_size_bytes=request_size,
            response_size_bytes=response_size,
        )
    except Exception as e:
        logger.error(f"[api_logging] Failed to log API usage: {e}")
