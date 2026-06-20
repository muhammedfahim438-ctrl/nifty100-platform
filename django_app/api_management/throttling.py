"""
api_management/throttling.py
Redis-backed rate limiting for channel partner API tiers.

Checks 3 windows simultaneously: per minute, per hour, per day.
Returns HTTP 429 with Retry-After header if any window is exceeded.

Tier limits (from settings.RATE_LIMITS):
  BASIC:      10/min,  100/hr,   500/day
  PRO:        60/min,  1000/hr,  10000/day
  ENTERPRISE: 300/min, 10000/hr, None (no daily cap)
"""
import time
from django.conf import settings
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled


WINDOWS = [
    ('minute', 60),
    ('hour',   3600),
    ('day',    86400),
]


class PartnerTierThrottle(BaseThrottle):
    """
    Multi-window rate limiter. Attach to any partner API view via:
        throttle_classes = [PartnerTierThrottle]
    """

    def allow_request(self, request, view):
        partner = getattr(request, 'user', None)
        if partner is None or not hasattr(partner, 'tier'):
            return True

        tier = partner.tier
        limits = settings.RATE_LIMITS.get(tier, settings.RATE_LIMITS['BASIC'])
        partner_id = str(partner.id)

        now = int(time.time())

        for window_name, window_seconds in WINDOWS:
            limit = limits.get(window_name)
            if limit is None:
                continue

            cache_key = f"ratelimit:{partner_id}:{window_name}"
            bucket_key = f"{cache_key}:start"

            bucket_start = cache.get(bucket_key)
            if bucket_start is None:
                cache.set(bucket_key, now, timeout=window_seconds)
                cache.set(cache_key, 1, timeout=window_seconds)
                count = 1
            else:
                count = cache.incr(cache_key)

            if count > limit:
                bucket_start = cache.get(bucket_key) or now
                retry_after = window_seconds - (now - bucket_start)
                self._throttle_data = {
                    'window': window_name,
                    'limit': limit,
                    'count': count,
                    'retry_after': max(1, retry_after),
                    'partner_id': partner_id,
                    'tier': tier,
                }
                return False

        return True

    def wait(self):
        data = getattr(self, '_throttle_data', {})
        return data.get('retry_after', 60)

    def throttled_response_data(self):
        data = getattr(self, '_throttle_data', {})
        partner_id = data.get('partner_id')
        tier = data.get('tier', 'BASIC')
        limits = settings.RATE_LIMITS.get(tier, {})

        remaining = {}
        for window_name, _ in WINDOWS:
            key = f"ratelimit:{partner_id}:{window_name}"
            count = cache.get(key) or 0
            limit = limits.get(window_name)
            if limit is not None:
                remaining[window_name] = max(0, limit - count)

        return {
            'error': 'rate_limit_exceeded',
            'message': f"Rate limit exceeded for {data.get('window')} window.",
            'tier': tier,
            'limits': limits,
            'remaining': remaining,
            'retry_after_seconds': data.get('retry_after', 60),
        }


class PublicAPIThrottle(BaseThrottle):
    """
    Simple anonymous throttle for the public /api/v1/ endpoints.
    100 calls per hour per IP.
    """
    LIMIT = 100
    WINDOW = 3600

    def allow_request(self, request, view):
        ip = self._get_ip(request)
        key = f"public_ratelimit:{ip}"
        count = cache.get(key, 0)
        if count >= self.LIMIT:
            self._retry_after = self.WINDOW
            return False
        cache.set(key, count + 1, timeout=self.WINDOW)
        return True

    def wait(self):
        return getattr(self, '_retry_after', self.WINDOW)

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')