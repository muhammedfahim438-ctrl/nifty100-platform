"""
api/serializers.py
DRF serializers for the public REST API (/api/v1/).
These power every Chart.js chart and table in the Django templates.
"""
from rest_framework import serializers
from companies.models import (
    DimCompany, DimSector, DimYear,
    FactProfitLoss, FactBalanceSheet, FactCashFlow,
    FactAnalysis, FactMLScore, FactProsCons, FactDocument,
)


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimSector
        fields = ['sector_id', 'sector_name', 'sector_code', 'description']


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company list / table views."""
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True, default=None)

    class Meta:
        model = DimCompany
        fields = [
            'symbol', 'company_name', 'sector_name', 'sub_sector',
            'company_logo', 'website', 'nse_url', 'bse_url',
            'roce_percentage', 'roe_percentage',
        ]


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Full company profile — used on /api/v1/companies/{symbol}/."""
    sector_name = serializers.CharField(source='sector.sector_name', read_only=True, default=None)

    class Meta:
        model = DimCompany
        fields = [
            'symbol', 'company_name', 'sector_name', 'sub_sector',
            'company_logo', 'website', 'nse_url', 'bse_url',
            'face_value', 'book_value', 'about_company',
            'roce_percentage', 'roe_percentage',
        ]


class ProfitLossSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True, default=None)

    class Meta:
        model = FactProfitLoss
        fields = [
            'year_label', 'sales', 'expenses', 'operating_profit', 'opm_pct',
            'other_income', 'interest', 'depreciation', 'profit_before_tax',
            'tax_pct', 'net_profit', 'eps', 'dividend_payout',
            'net_profit_margin_pct', 'expense_ratio_pct', 'interest_coverage',
        ]


class BalanceSheetSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True, default=None)

    class Meta:
        model = FactBalanceSheet
        fields = [
            'year_label', 'equity_capital', 'reserves', 'borrowings',
            'other_liabilities', 'total_liabilities', 'fixed_assets',
            'cwip', 'investments', 'other_assets', 'total_assets',
            'debt_to_equity', 'equity_ratio', 'book_value_per_share',
        ]


class CashFlowSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source='year.year_label', read_only=True, default=None)

    class Meta:
        model = FactCashFlow
        fields = [
            'year_label', 'operating_activity', 'investing_activity',
            'financing_activity', 'net_cash_flow', 'free_cash_flow',
            'cash_conversion_ratio',
        ]


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactAnalysis
        fields = [
            'period_label', 'compounded_sales_growth_pct',
            'compounded_profit_growth_pct', 'stock_price_cagr_pct', 'roe_pct',
        ]


class MLScoreSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source='company.company_name', read_only=True, default=None)
    sector_name = serializers.CharField(source='company.sector.sector_name', read_only=True, default=None)

    class Meta:
        model = FactMLScore
        fields = [
            'symbol', 'company_name', 'sector_name', 'computed_at',
            'overall_score', 'profitability_score', 'growth_score',
            'leverage_score', 'cashflow_score', 'dividend_score',
            'trend_score', 'health_label',
        ]


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactProsCons
        fields = ['is_pro', 'category', 'text', 'source', 'confidence']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactDocument
        fields = ['year', 'annual_report']


class CompanyFinancialsSerializer(serializers.Serializer):
    """
    Composite serializer for /api/v1/companies/{symbol}/financials/
    Bundles everything the company detail page's Chart.js calls need
    into a single response (avoids 6+ separate API round trips).
    """
    profit_loss = ProfitLossSerializer(many=True)
    balance_sheet = BalanceSheetSerializer(many=True)
    cash_flow = CashFlowSerializer(many=True)
    analysis = AnalysisSerializer(many=True)
    ml_score = MLScoreSerializer(allow_null=True)
    pros_cons = ProsConsSerializer(many=True)
    documents = DocumentSerializer(many=True)


class ScreenerResultSerializer(serializers.Serializer):
    """Flat result row used by /api/v1/screener/ and the screener page."""
    symbol = serializers.CharField()
    company_name = serializers.CharField()
    sector_name = serializers.CharField(allow_null=True)
    overall_score = serializers.FloatField(allow_null=True)
    health_label = serializers.CharField(allow_null=True)
    opm_pct = serializers.FloatField(allow_null=True)
    debt_to_equity = serializers.FloatField(allow_null=True)
    roe_pct = serializers.FloatField(allow_null=True)
