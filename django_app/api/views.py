"""
api/views.py
Public REST API (/api/v1/) — powers every Chart.js chart and table
across the Django template pages (home, company list, company detail,
screener, compare, sector detail, health scores).

No authentication required — these are public, read-only endpoints
for the website itself. Rate-limited at 100 req/hr per IP via
PublicAPIThrottle (see api_management/throttling.py).
"""
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api_management.throttling import PublicAPIThrottle
from companies.models import (
    DimCompany, DimSector,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons, FactDocument,
)
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer, SectorSerializer,
    ProfitLossSerializer, BalanceSheetSerializer, CashFlowSerializer,
    AnalysisSerializer, MLScoreSerializer, ProsConsSerializer, DocumentSerializer,
)


class PublicAPIBaseView(APIView):
    """Base class applying the public rate limit to every endpoint below."""
    throttle_classes = [PublicAPIThrottle]


# ─── COMPANIES ──────────────────────────────────────────────────────────────────

@extend_schema(tags=['Public API'], summary='List all companies')
class CompanyListView(PublicAPIBaseView):
    def get(self, request):
        qs = DimCompany.objects.select_related('sector').all().order_by('company_name')
        sector = request.query_params.get('sector')
        if sector:
            qs = qs.filter(sector__sector_name__iexact=sector)
        data = CompanyListSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})


@extend_schema(tags=['Public API'], summary='Single company profile')
class CompanyDetailView(PublicAPIBaseView):
    def get(self, request, symbol):
        try:
            company = DimCompany.objects.select_related('sector').get(symbol=symbol.upper())
        except DimCompany.DoesNotExist:
            return Response({'error': f'Company {symbol} not found.'}, status=404)
        return Response(CompanyDetailSerializer(company).data)


@extend_schema(tags=['Public API'], summary='Full financial history for one company')
class CompanyFinancialsView(PublicAPIBaseView):
    """
    Bundles P&L, Balance Sheet, Cash Flow, Analysis (CAGR), ML Score,
    Pros/Cons, and Documents into a single response.
    This is the endpoint company_detail.html's JS calls on page load.
    """
    def get(self, request, symbol):
        symbol = symbol.upper()
        try:
            company = DimCompany.objects.get(symbol=symbol)
        except DimCompany.DoesNotExist:
            return Response({'error': f'Company {symbol} not found.'}, status=404)

        pl = FactProfitLoss.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order')
        bs = FactBalanceSheet.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order')
        cf = FactCashFlow.objects.filter(symbol=symbol).select_related('year').order_by('year__sort_order')
        analysis = FactAnalysis.objects.filter(symbol=symbol)
        pros_cons = FactProsCons.objects.filter(symbol=symbol)
        documents = FactDocument.objects.filter(symbol=symbol).order_by('-year')

        ml_score = None
        try:
            score_obj = FactMLScore.objects.get(company_id=symbol)
            ml_score = MLScoreSerializer(score_obj).data
        except FactMLScore.DoesNotExist:
            pass

        return Response({
            'symbol': symbol,
            'company_name': company.company_name,
            'profit_loss': ProfitLossSerializer(pl, many=True).data,
            'balance_sheet': BalanceSheetSerializer(bs, many=True).data,
            'cash_flow': CashFlowSerializer(cf, many=True).data,
            'analysis': AnalysisSerializer(analysis, many=True).data,
            'ml_score': ml_score,
            'pros_cons': ProsConsSerializer(pros_cons, many=True).data,
            'documents': DocumentSerializer(documents, many=True).data,
        })


# ─── SECTORS ────────────────────────────────────────────────────────────────────

@extend_schema(tags=['Public API'], summary='List all sectors')
class SectorListView(PublicAPIBaseView):
    def get(self, request):
        qs = DimSector.objects.all().order_by('sector_name')
        data = SectorSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})


# ─── ML SCORES ──────────────────────────────────────────────────────────────────

@extend_schema(tags=['Public API'], summary='All ML health scores')
class ScoresListView(PublicAPIBaseView):
    def get(self, request):
        qs = FactMLScore.objects.select_related('company', 'company__sector').order_by('-overall_score')
        symbols = request.query_params.get('symbols')
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            qs = qs.filter(company_id__in=symbol_list)
        data = MLScoreSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})


# ─── SCREENER ───────────────────────────────────────────────────────────────────

@extend_schema(
    tags=['Public API'],
    summary='Filter companies by financial criteria',
    parameters=[
        OpenApiParameter('sector', str), OpenApiParameter('health_label', str),
        OpenApiParameter('min_score', float), OpenApiParameter('min_roe', float),
        OpenApiParameter('max_de', float), OpenApiParameter('min_sales_growth', float),
    ],
)
class ScreenerView(PublicAPIBaseView):
    """
    Dynamic query builder — only applies filters the user actually set,
    using Q() objects as specified in the project spec.
    """
    def get(self, request):
        sector = request.query_params.get('sector')
        health_label = request.query_params.get('health_label')
        min_score = request.query_params.get('min_score')
        min_roe = request.query_params.get('min_roe')
        max_de = request.query_params.get('max_de')
        min_growth = request.query_params.get('min_sales_growth')

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

            # Latest year balance sheet / P&L for D/E, OPM, ROE checks
            latest_bs = (
                FactBalanceSheet.objects
                .filter(symbol=company.symbol)
                .exclude(year__is_ttm=True)
                .order_by('-year__sort_order')
                .first()
            )
            latest_pl = (
                FactProfitLoss.objects
                .filter(symbol=company.symbol)
                .exclude(year__is_ttm=True)
                .order_by('-year__sort_order')
                .first()
            )

            de = latest_bs.debt_to_equity if latest_bs else None
            opm = latest_pl.opm_pct if latest_pl else None
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
                'opm_pct': opm,
                'debt_to_equity': de,
                'roe_pct': roe,
            })

        return Response({'count': len(results), 'results': results})
