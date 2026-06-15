"""
API Views for the Nifty 100 Financial Intelligence Platform.
"""

from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response

from companies.models import (
    DimCompany, DimSector, FactProfitLoss,
    FactBalanceSheet, FactCashFlow, FactMLScore,
    FactProsCons, FactDocument
)
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer,
    SectorSerializer, ProfitLossSerializer,
    BalanceSheetSerializer, CashFlowSerializer,
    MLScoreSerializer, ProsConsSerializer, DocumentSerializer
)


class CompanyListView(generics.ListAPIView):
    serializer_class   = CompanyListSerializer
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["symbol", "company_name"]
    ordering_fields    = ["symbol", "company_name"]
    ordering           = ["symbol"]
    pagination_class   = None

    def get_queryset(self):
        queryset = DimCompany.objects.select_related("sector").all()

        sector = self.request.query_params.get("sector")
        if sector:
            queryset = queryset.filter(sector__sector_name__iexact=sector)

        return queryset


class CompanyDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/companies/{symbol}/
    Returns full company details.
    """
    serializer_class   = CompanyDetailSerializer
    queryset           = DimCompany.objects.select_related("sector").all()
    lookup_field       = "symbol"


class CompanyFinancialsView(generics.GenericAPIView):
    """
    GET /api/v1/companies/{symbol}/financials/
    Returns all financial data for one company.
    """
    def get(self, request, symbol):
        try:
            company = DimCompany.objects.get(symbol=symbol)
        except DimCompany.DoesNotExist:
            return Response({"error": f"Company {symbol} not found"}, status=404)

        profit_loss   = FactProfitLoss.objects.filter(symbol=company).select_related("year").order_by("year__sort_order")
        balance_sheet = FactBalanceSheet.objects.filter(symbol=company).select_related("year").order_by("year__sort_order")
        cash_flow     = FactCashFlow.objects.filter(symbol=company).select_related("year").order_by("year__sort_order")
        ml_score      = FactMLScore.objects.filter(symbol=company).order_by("-computed_at").first()
        pros_cons     = FactProsCons.objects.filter(symbol=company)
        documents     = FactDocument.objects.filter(symbol=company).order_by("-year")

        return Response({
            "symbol"       : symbol,
            "company_name" : company.company_name,
            "profit_loss"  : ProfitLossSerializer(profit_loss, many=True).data,
            "balance_sheet": BalanceSheetSerializer(balance_sheet, many=True).data,
            "cash_flow"    : CashFlowSerializer(cash_flow, many=True).data,
            "ml_score"     : MLScoreSerializer(ml_score).data if ml_score else None,
            "pros"         : ProsConsSerializer(pros_cons.filter(is_pro=True), many=True).data,
            "cons"         : ProsConsSerializer(pros_cons.filter(is_pro=False), many=True).data,
            "documents"    : DocumentSerializer(documents, many=True).data,
        })


class SectorListView(generics.ListAPIView):
    """
    GET /api/v1/sectors/
    Returns list of all sectors.
    """
    serializer_class = SectorSerializer
    queryset         = DimSector.objects.all().order_by("sector_name")


class HealthScoreListView(generics.ListAPIView):
    """
    GET /api/v1/scores/
    Returns latest health scores for all companies.
    Supports filtering by health_label.
    """
    serializer_class = MLScoreSerializer

    def get_queryset(self):
        queryset = FactMLScore.objects.select_related("symbol").order_by("-overall_score")

        label = self.request.query_params.get("label")
        if label:
            queryset = queryset.filter(health_label__iexact=label)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for score in queryset:
            row = MLScoreSerializer(score).data
            row["symbol"]       = score.symbol_id
            row["company_name"] = score.symbol.company_name
            data.append(row)
        return Response(data)


@api_view(["GET"])
def screener_view(request):
    """
    GET /api/v1/screener/
    Filter companies by financial criteria.

    Query params:
        min_score       — minimum ML health score (0-100)
        health_label    — EXCELLENT / GOOD / AVERAGE / WEAK / POOR
        sector          — sector name (case-insensitive)
        min_roe         — minimum ROE% (from dim_company.roe_pct)
        max_de          — maximum Debt-to-Equity (from fact_balance_sheet latest year)
    """
    companies = DimCompany.objects.select_related("sector").all()

    # ── Sector filter ────────────────────────────────────────────────────────
    sector = request.query_params.get("sector")
    if sector:
        companies = companies.filter(sector__sector_name__iexact=sector)

    # ── ROE filter — dim_company.roe_pct ─────────────────────────────────────
    min_roe = request.query_params.get("min_roe")
    if min_roe:
        try:
            companies = companies.filter(roe_pct__gte=float(min_roe))
        except ValueError:
            pass  # ignore malformed value

    # ── Health score / label filter — fact_ml_scores ─────────────────────────
    health_label = request.query_params.get("health_label")
    min_score    = request.query_params.get("min_score")

    if health_label or min_score:
        score_qs = FactMLScore.objects.all()
        if health_label:
            score_qs = score_qs.filter(health_label__iexact=health_label)
        if min_score:
            try:
                score_qs = score_qs.filter(overall_score__gte=float(min_score))
            except ValueError:
                pass
        valid_symbols = score_qs.values_list("symbol_id", flat=True)
        companies = companies.filter(symbol__in=valid_symbols)

    # ── Max D/E filter — fact_balance_sheet latest non-TTM year ─────────────
    max_de = request.query_params.get("max_de")
    if max_de:
        try:
            max_de_val = float(max_de)
            # Get latest non-TTM balance sheet row per company, filter by D/E
            de_symbols = (
                FactBalanceSheet.objects
                .filter(year__is_ttm=False, debt_to_equity__isnull=False)
                .filter(debt_to_equity__lte=max_de_val)
                .order_by("symbol_id", "-year__sort_order")
                .distinct("symbol_id")
                .values_list("symbol_id", flat=True)
            )
            companies = companies.filter(symbol__in=list(de_symbols))
        except ValueError:
            pass

    serializer = CompanyListSerializer(companies, many=True)
    return Response({
        "count"  : companies.count(),
        "results": serializer.data
    })