"""
api_management/partner_views.py
Channel Partner REST API — HMAC-authenticated views for paying partners.

Authentication: Every request must include:
  X-API-Key-ID   : UUID of the partner's public key
  X-Timestamp    : Unix timestamp (rejected if >300s old)
  X-Nonce        : Random UUID to prevent replay attacks
  X-Signature    : HMAC-SHA256(method + url + timestamp + body_hash, key_secret)

Rate limiting: PartnerTierThrottle checks 3 windows (minute/hour/day)
               based on the partner's tier (BASIC / PRO / ENTERPRISE).
"""
import hashlib
import hmac
import json
import logging
import time
import secrets as secrets_mod

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
try:
    from drf_spectacular.utils import extend_schema, OpenApiParameter
except Exception:  # pragma: no cover - optional dev dependency
    # Provide no-op fallbacks when drf-spectacular isn't installed (e.g. in lints/CI)
    def extend_schema(*a, **k):
        def _decorator(f):
            return f
        return _decorator

    class OpenApiParameter:  # minimal placeholder
        def __init__(self, *args, **kwargs):
            pass

from .models import ChannelPartner, APIKey, WebhookEndpoint, WebhookEvent
from .serializers import (
    APIKeySerializer, WebhookEndpointSerializer, WebhookEventSerializer,
)
from .throttling import PartnerTierThrottle
from companies.models import (
    DimCompany, FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons, FactDocument,
)

logger = logging.getLogger(__name__)

NONCE_CACHE = {}   # In production, store nonces in Redis with TTL


# ─── HMAC Authentication ───────────────────────────────────────────────────────

def authenticate_partner(request):
    """
    Validates the HMAC-SHA256 signature on a partner API request.
    Returns (api_key_obj, partner_obj) on success or raises ValueError with message.
    """
    key_id    = request.headers.get('X-API-Key-ID')
    timestamp = request.headers.get('X-Timestamp')
    nonce     = request.headers.get('X-Nonce')
    signature = request.headers.get('X-Signature')

    if not all([key_id, timestamp, nonce, signature]):
        raise ValueError("Missing required authentication headers: X-API-Key-ID, X-Timestamp, X-Nonce, X-Signature")

    # Reject stale requests (>300 seconds old)
    try:
        ts = int(timestamp)
    except ValueError:
        raise ValueError("X-Timestamp must be a Unix integer timestamp")

    if abs(time.time() - ts) > 300:
        raise ValueError("Request timestamp is too old or too far in the future (max 300 seconds)")

    # Prevent replay attacks — nonce must not have been seen before
    if nonce in NONCE_CACHE:
        raise ValueError("Nonce has already been used (replay attack detected)")

    # Look up API key
    try:
        api_key = APIKey.objects.select_related('partner').get(key_id=key_id, is_active=True)
    except APIKey.DoesNotExist:
        raise ValueError("API key not found or inactive")

    if api_key.is_expired():
        raise ValueError("API key has expired")

    if not api_key.partner.is_active:
        raise ValueError("Partner account is inactive")

    # Reconstruct expected signature
    body = request.body or b''
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{request.method}\n{request.path}\n{timestamp}\n{body_hash}"

    # We can't reverse bcrypt, so we store the raw secret separately in a
    # side-channel for HMAC. Here we use the bcrypt hash itself as a stable
    # key — in production you'd store an additional HMAC-specific secret.
    # For now, derive a consistent key from the stored hash.
    expected = hmac.new(
        api_key.key_secret_hash.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not secrets_mod.compare_digest(expected, signature):
        raise ValueError("Signature verification failed")

    # Record nonce and update last_used_at
    NONCE_CACHE[nonce] = time.time()
    api_key.last_used_at = timezone.now()
    api_key.save(update_fields=['last_used_at'])

    return api_key, api_key.partner


class PartnerAPIBaseView(APIView):
    """Base class — authenticate every partner request via HMAC."""
    throttle_classes = [PartnerTierThrottle]

    def _auth(self, request):
        """Returns (api_key, partner) or sends a 401 Response."""
        if getattr(request, '_auth_error', None):
            return None, request._auth_error
        return getattr(request, 'api_key', None), None

    def dispatch(self, request, *args, **kwargs):
        start_time = time.time()
        
        request_size = 0
        try:
            if request.body:
                request_size = len(request.body)
        except Exception:
            pass

        # Perform authentication early so throttle has access to request.user
        try:
            api_key, partner = authenticate_partner(request)
            request.user = partner
            request.api_key = api_key
            auth_error = None
        except ValueError as e:
            request.user = None
            request.api_key = None
            auth_error = Response(
                {'error': 'authentication_failed', 'message': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        request._auth_error = auth_error

        response = super().dispatch(request, *args, **kwargs)

        response_time_ms = int((time.time() - start_time) * 1000)

        response_size = 0
        try:
            if hasattr(response, 'rendered_content'):
                response_size = len(response.rendered_content)
            elif hasattr(response, 'content'):
                response_size = len(response.content)
        except Exception:
            pass

        key_id = request.headers.get('X-API-Key-ID')
        if key_id:
            ip_address = None
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            from .tasks import log_api_usage
            log_api_usage.delay(
                key_id=key_id,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
                request_size=request_size,
                response_size=response_size
            )

        return response


# ─── Company Data Endpoints ─────────────────────────────────────────────────────

@extend_schema(tags=['Partner API'], summary='Full company data dump')
class PartnerCompanyFullView(PartnerAPIBaseView):
    """GET /api/partner/v1/companies/{symbol}/full/"""

    def get(self, request, symbol):
        _, err = self._auth(request)
        if err:
            return err

        symbol = symbol.upper()
        try:
            company = DimCompany.objects.select_related('sector').get(symbol=symbol)
        except DimCompany.DoesNotExist:
            return Response({'error': f'Company {symbol} not found'}, status=404)

        pl = list(FactProfitLoss.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order').values())
        bs = list(FactBalanceSheet.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order').values())
        cf = list(FactCashFlow.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order').values())
        analysis = list(FactAnalysis.objects.filter(symbol=symbol).values())
        pros_cons = list(FactProsCons.objects.filter(symbol=symbol).values())
        documents = list(FactDocument.objects.filter(symbol=symbol).order_by('-year').values())

        ml_score = None
        try:
            score = FactMLScore.objects.get(company_id=symbol)
            ml_score = {
                'overall_score': score.overall_score,
                'profitability_score': score.profitability_score,
                'growth_score': score.growth_score,
                'leverage_score': score.leverage_score,
                'cashflow_score': score.cashflow_score,
                'dividend_score': score.dividend_score,
                'trend_score': score.trend_score,
                'health_label': score.health_label,
                'computed_at': score.computed_at,
            }
        except FactMLScore.DoesNotExist:
            pass

        return Response({
            'symbol': company.symbol,
            'company_name': company.company_name,
            'sector': company.sector.sector_name if company.sector else None,
            'website': company.website,
            'nse_url': company.nse_url,
            'bse_url': company.bse_url,
            'face_value': company.face_value,
            'book_value': company.book_value,
            'roce_percentage': company.roce_percentage,
            'roe_percentage': company.roe_percentage,
            'about_company': company.about_company,
            'ml_score': ml_score,
            'profit_loss': pl,
            'balance_sheet': bs,
            'cash_flow': cf,
            'analysis': analysis,
            'pros_cons': pros_cons,
            'documents': documents,
        })


@extend_schema(
    tags=['Partner API'],
    summary='Bulk financials for up to 10 companies',
    parameters=[OpenApiParameter('symbols', str, description='Comma-separated list of symbols, max 10')],
)
class PartnerBulkFinancialsView(PartnerAPIBaseView):
    """GET /api/partner/v1/bulk-financials/?symbols=TCS,INFY,WIPRO"""

    def get(self, request):
        _, err = self._auth(request)
        if err:
            return err

        symbols_param = request.query_params.get('symbols', '')
        symbol_list = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]

        if not symbol_list:
            return Response({'error': 'Provide ?symbols=TCS,INFY (max 10)'}, status=400)

        if len(symbol_list) > 10:
            return Response({'error': 'Maximum 10 symbols per bulk request'}, status=400)

        results = []
        for symbol in symbol_list:
            try:
                company = DimCompany.objects.get(symbol=symbol)
            except DimCompany.DoesNotExist:
                results.append({'symbol': symbol, 'error': 'not found'})
                continue

            latest_pl = (
                FactProfitLoss.objects.filter(symbol=symbol)
                .exclude(year__is_ttm=True)
                .order_by('-year__sort_order')
                .first()
            )
            latest_bs = (
                FactBalanceSheet.objects.filter(symbol=symbol)
                .exclude(year__is_ttm=True)
                .order_by('-year__sort_order')
                .first()
            )
            ml = None
            try:
                ml = FactMLScore.objects.get(company_id=symbol)
            except FactMLScore.DoesNotExist:
                pass

            results.append({
                'symbol': symbol,
                'company_name': company.company_name,
                'latest_sales': latest_pl.sales if latest_pl else None,
                'latest_net_profit': latest_pl.net_profit if latest_pl else None,
                'latest_opm_pct': latest_pl.opm_pct if latest_pl else None,
                'latest_debt_to_equity': latest_bs.debt_to_equity if latest_bs else None,
                'roe_percentage': company.roe_percentage,
                'overall_score': ml.overall_score if ml else None,
                'health_label': ml.health_label if ml else None,
            })

        return Response({'count': len(results), 'results': results})


@extend_schema(
    tags=['Partner API'],
    summary='Screener — filter companies by financial criteria',
    parameters=[
        OpenApiParameter('sector', str), OpenApiParameter('health_label', str),
        OpenApiParameter('min_score', float), OpenApiParameter('min_roe', float),
        OpenApiParameter('max_de', float), OpenApiParameter('min_sales_growth', float),
    ],
)
class PartnerScreenerView(PartnerAPIBaseView):
    """GET /api/partner/v1/screener/"""

    def get(self, request):
        _, err = self._auth(request)
        if err:
            return err

        sector      = request.query_params.get('sector')
        health_label = request.query_params.get('health_label')
        min_score   = request.query_params.get('min_score')
        min_roe     = request.query_params.get('min_roe')
        max_de      = request.query_params.get('max_de')
        min_growth  = request.query_params.get('min_sales_growth')

        scores_qs = FactMLScore.objects.select_related('company', 'company__sector')

        if sector:
            scores_qs = scores_qs.filter(company__sector__sector_name__iexact=sector)
        if health_label:
            scores_qs = scores_qs.filter(health_label__iexact=health_label)
        if min_score:
            scores_qs = scores_qs.filter(overall_score__gte=float(min_score))

        results = []
        for score in scores_qs[:200]:
            company = score.company
            if company is None:
                continue

            latest_bs = (
                FactBalanceSheet.objects.filter(symbol=company.symbol)
                .exclude(year__is_ttm=True)
                .order_by('-year__sort_order')
                .first()
            )
            de = latest_bs.debt_to_equity if latest_bs else None
            roe = company.roe_percentage

            if max_de is not None and de is not None and de > float(max_de):
                continue
            if min_roe is not None and (roe is None or roe < float(min_roe)):
                continue
            if min_growth:
                growth_row = FactAnalysis.objects.filter(
                    symbol=company.symbol, period_label='3Y'
                ).first()
                growth_val = growth_row.compounded_sales_growth_pct if growth_row else None
                if growth_val is None or growth_val < float(min_growth):
                    continue

            results.append({
                'symbol': company.symbol,
                'company_name': company.company_name,
                'sector_name': company.sector.sector_name if company.sector else None,
                'overall_score': score.overall_score,
                'health_label': score.health_label,
                'debt_to_equity': de,
                'roe_pct': roe,
            })

        return Response({'count': len(results), 'results': results})


@extend_schema(tags=['Partner API'], summary='Get ML health scores')
class PartnerScoresView(PartnerAPIBaseView):
    """GET /api/partner/v1/scores/?symbols=TCS,INFY"""

    def get(self, request):
        _, err = self._auth(request)
        if err:
            return err

        qs = FactMLScore.objects.select_related('company', 'company__sector').order_by('-overall_score')
        symbols = request.query_params.get('symbols')
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            qs = qs.filter(company_id__in=symbol_list)

        results = []
        for s in qs:
            results.append({
                'symbol': s.symbol,
                'company_name': s.company.company_name if s.company else None,
                'overall_score': s.overall_score,
                'profitability_score': s.profitability_score,
                'growth_score': s.growth_score,
                'leverage_score': s.leverage_score,
                'cashflow_score': s.cashflow_score,
                'dividend_score': s.dividend_score,
                'trend_score': s.trend_score,
                'health_label': s.health_label,
                'computed_at': s.computed_at,
            })

        return Response({'count': len(results), 'results': results})


# ─── API Key Management ─────────────────────────────────────────────────────────

@extend_schema(tags=['Partner API'], summary='List and create API keys')
class PartnerKeyListView(PartnerAPIBaseView):
    """GET /POST /api/partner/v1/keys/"""

    def get(self, request):
        api_key, err = self._auth(request)
        if err:
            return err
        keys = APIKey.objects.filter(partner=api_key.partner, is_active=True)
        return Response(APIKeySerializer(keys, many=True).data)

    def post(self, request):
        api_key, err = self._auth(request)
        if err:
            return err
        label = request.data.get('label', 'Default Key')
        new_key, raw_secret = APIKey.create_key_pair(api_key.partner, label=label)
        return Response({
            'key_id': str(new_key.key_id),
            'label': new_key.label,
            'key_secret': raw_secret,  # Shown ONCE only — never stored in plain text
            'warning': 'Save the key_secret now. It will never be shown again.',
            'created_at': new_key.created_at,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Partner API'], summary='Delete an API key')
class PartnerKeyDetailView(PartnerAPIBaseView):
    """DELETE /api/partner/v1/keys/{key_id}/"""

    def delete(self, request, key_id):
        api_key, err = self._auth(request)
        if err:
            return err
        try:
            key = APIKey.objects.get(key_id=key_id, partner=api_key.partner)
            key.is_active = False
            key.save(update_fields=['is_active'])
            return Response({'message': f'Key {key_id} deactivated.'})
        except APIKey.DoesNotExist:
            return Response({'error': 'Key not found'}, status=404)


# ─── Webhook Management ─────────────────────────────────────────────────────────

@extend_schema(tags=['Partner API'], summary='List and register webhooks')
class PartnerWebhookListView(PartnerAPIBaseView):
    """GET /POST /api/partner/v1/webhooks/"""

    def get(self, request):
        api_key, err = self._auth(request)
        if err:
            return err
        wh = WebhookEndpoint.objects.filter(partner=api_key.partner, is_active=True)
        return Response(WebhookEndpointSerializer(wh, many=True).data)

    def post(self, request):
        api_key, err = self._auth(request)
        if err:
            return err
        url = request.data.get('url')
        event_type = request.data.get('event_type')
        if not url or not event_type:
            return Response({'error': 'url and event_type are required'}, status=400)

        valid_events = ['score_updated', 'anomaly_flagged']
        if event_type not in valid_events:
            return Response({'error': f'event_type must be one of {valid_events}'}, status=400)

        # Generate a webhook signing secret
        webhook_secret = secrets_mod.token_hex(32)
        wh = WebhookEndpoint.objects.create(
            partner=api_key.partner,
            url=url,
            event_type=event_type,
            secret=webhook_secret,
        )
        return Response({
            'id': wh.id,
            'url': wh.url,
            'event_type': wh.event_type,
            'signing_secret': webhook_secret,
            'warning': 'Save the signing_secret now. It will not be shown again.',
            'created_at': wh.created_at,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Partner API'], summary='Delete a webhook endpoint')
class PartnerWebhookDetailView(PartnerAPIBaseView):
    """DELETE /api/partner/v1/webhooks/{pk}/"""

    def delete(self, request, pk):
        api_key, err = self._auth(request)
        if err:
            return err
        try:
            wh = WebhookEndpoint.objects.get(pk=pk, partner=api_key.partner)
            wh.is_active = False
            wh.save(update_fields=['is_active'])
            return Response({'message': f'Webhook {pk} deactivated.'})
        except WebhookEndpoint.DoesNotExist:
            return Response({'error': 'Webhook not found'}, status=404)
