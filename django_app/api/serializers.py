"""
Serializers for the Nifty 100 Financial Intelligence API.
Converts Django model instances to JSON and back.
"""

from rest_framework import serializers
from companies.models import (
    DimCompany, DimSector, FactProfitLoss,
    FactBalanceSheet, FactCashFlow, FactMLScore,
    FactProsCons, FactDocument
)


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DimSector
        fields = ["sector_id", "sector_name", "sector_code"]


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company list page."""
    sector_name  = serializers.CharField(source="sector.sector_name", default=None)
    health_label = serializers.SerializerMethodField()
    overall_score= serializers.SerializerMethodField()

    class Meta:
        model  = DimCompany
        fields = [
            "symbol", "company_name", "sector_name",
            "company_logo", "website", "roce_pct", "roe_pct",
            "health_label", "overall_score"
        ]

    def get_health_label(self, obj):
        score = FactMLScore.objects.filter(symbol=obj).order_by("-computed_at").first()
        if not score:
            return None
        return score.health_label

    def get_overall_score(self, obj):
        score = FactMLScore.objects.filter(symbol=obj).order_by("-computed_at").first()
        if not score or score.overall_score is None:
            return None
        try:
            val = float(score.overall_score)
            import math
            return None if math.isnan(val) else round(val, 2)
        except (TypeError, ValueError):
            return None


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Full serializer for company detail page."""
    sector_name = serializers.CharField(source="sector.sector_name", default=None)

    class Meta:
        model  = DimCompany
        fields = "__all__"


class ProfitLossSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label", default=None)
    fiscal_year= serializers.IntegerField(source="year.fiscal_year", default=None)

    class Meta:
        model  = FactProfitLoss
        fields = [
            "year_label", "fiscal_year", "sales", "expenses",
            "operating_profit", "opm_pct", "other_income",
            "interest", "depreciation", "profit_before_tax",
            "tax_pct", "net_profit", "eps", "dividend_payout",
            "net_profit_margin_pct", "expense_ratio_pct", "interest_coverage"
        ]


class BalanceSheetSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label", default=None)
    fiscal_year= serializers.IntegerField(source="year.fiscal_year", default=None)

    class Meta:
        model  = FactBalanceSheet
        fields = [
            "year_label", "fiscal_year", "equity_capital", "reserves",
            "borrowings", "other_liabilities", "total_liabilities",
            "fixed_assets", "cwip", "investments", "other_asset",
            "total_assets", "debt_to_equity", "equity_ratio"
        ]


class CashFlowSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label", default=None)
    fiscal_year= serializers.IntegerField(source="year.fiscal_year", default=None)

    class Meta:
        model  = FactCashFlow
        fields = [
            "year_label", "fiscal_year", "operating_activity",
            "investing_activity", "financing_activity",
            "net_cash_flow", "free_cash_flow"
        ]


class MLScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FactMLScore
        fields = [
            "overall_score", "profitability_score", "growth_score",
            "leverage_score", "cashflow_score", "dividend_score",
            "trend_score", "health_label", "computed_at"
        ]


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FactProsCons
        fields = ["is_pro", "text", "source"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FactDocument
        fields = ["year", "annual_report"]