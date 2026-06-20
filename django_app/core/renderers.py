"""
core/renderers.py
Custom DRF JSON renderer that safely converts Python float NaN / Inf to null
instead of crashing with "Out of range float values are not JSON compliant".

This is needed because our PostgreSQL warehouse contains a handful of
NaN/Inf values (e.g. TVSMOTOR roce_pct) that were computed during ETL
and stored as IEEE-754 NaN in Postgres FLOAT8 columns. Python's psycopg2
driver may return these as float('nan') OR decimal.Decimal('NaN') depending
on column type. Both crash the stdlib json module. This renderer converts
NaN/Inf to null at the HTTP serialization layer without touching the database.
"""
import math
import decimal

from rest_framework.renderers import JSONRenderer


def _sanitize(obj):
    """Recursively walk a Python object and replace NaN/Inf floats with None."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, decimal.Decimal):
        # Decimal('NaN'), Decimal('Infinity'), Decimal('-Infinity') -> null
        if obj.is_nan() or obj.is_infinite():
            return None
        return float(obj)  # Convert finite Decimal to float for JSON
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


class NaNSafeJSONRenderer(JSONRenderer):
    """
    Replaces the default DRF JSONRenderer. Sanitizes all float NaN/Inf values
    in the response data before encoding to JSON, preventing ValueError crashes.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        safe_data = _sanitize(data)
        return super().render(safe_data, accepted_media_type, renderer_context)
