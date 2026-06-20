"""
companies/models.py
Django models mapping to the EXISTING PostgreSQL star-schema warehouse.
All models use managed=False — Django will NEVER create, alter, or drop
these tables. They are read against tables already created by your ETL
pipeline (etl/03_load_to_warehouse.py).

CONFIRMED from \\d fact_profit_loss on 2026-06-20:
  - The join column in all fact tables is `symbol` (NOT company_id)
  - fact_profit_loss has a UNIQUE constraint on (symbol, year_id)
  - FK: fact_profit_loss.symbol -> dim_company.symbol
  - FK: fact_profit_loss.year_id -> dim_year.year_id
  - Primary key on all fact tables is `id` (AutoField/SERIAL)
"""
from django.db import models


# ─── DIMENSION TABLES ──────────────────────────────────────────────────────────

class DimSector(models.Model):
    sector_id = models.IntegerField(primary_key=True)
    sector_name = models.CharField(max_length=100)
    sector_code = models.CharField(max_length=20, null=True, blank=True)


    class Meta:
        managed = False
        db_table = 'dim_sector'

    def __str__(self):
        return self.sector_name


class DimCompany(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    company_name = models.CharField(max_length=255)
    sector = models.ForeignKey(
        DimSector, on_delete=models.DO_NOTHING, db_column='sector_id',
        null=True, blank=True, related_name='companies'
    )

    company_logo = models.CharField(max_length=500, null=True, blank=True)
    website = models.CharField(max_length=500, null=True, blank=True)
    nse_url = models.CharField(max_length=500, null=True, blank=True)
    bse_url = models.CharField(max_length=500, null=True, blank=True)
    face_value = models.FloatField(null=True, blank=True)
    book_value = models.FloatField(null=True, blank=True)
    about_company = models.TextField(null=True, blank=True)
    roce_percentage = models.FloatField(db_column='roce_pct', null=True, blank=True)
    roe_percentage = models.FloatField(db_column='roe_pct', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'dim_company'

    def __str__(self):
        return f"{self.symbol} — {self.company_name}"


class DimYear(models.Model):
    year_id = models.IntegerField(primary_key=True)
    year_label = models.CharField(max_length=20)   # e.g. 'Mar 2024'
    fiscal_year = models.IntegerField(null=True, blank=True)
    quarter = models.CharField(max_length=5, null=True, blank=True)
    is_ttm = models.BooleanField(default=False)
    is_half_year = models.BooleanField(default=False)
    sort_order = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'dim_year'
        ordering = ['sort_order']

    def __str__(self):
        return self.year_label


class DimHealthLabel(models.Model):
    label_id = models.IntegerField(primary_key=True)
    label_name = models.CharField(max_length=20)  # EXCELLENT/GOOD/AVERAGE/WEAK/POOR
    min_score = models.FloatField()
    max_score = models.FloatField()
    color_hex = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'dim_health_label'

    def __str__(self):
        return self.label_name


# ─── FACT TABLES ────────────────────────────────────────────────────────────────

class FactProfitLoss(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    year = models.ForeignKey(DimYear, on_delete=models.DO_NOTHING, db_column='year_id', null=True)
    sales = models.FloatField(null=True, blank=True)
    expenses = models.FloatField(null=True, blank=True)
    operating_profit = models.FloatField(null=True, blank=True)
    opm_pct = models.FloatField(null=True, blank=True)
    other_income = models.FloatField(null=True, blank=True)
    interest = models.FloatField(null=True, blank=True)
    depreciation = models.FloatField(null=True, blank=True)
    profit_before_tax = models.FloatField(null=True, blank=True)
    tax_pct = models.FloatField(null=True, blank=True)
    net_profit = models.FloatField(null=True, blank=True)
    eps = models.FloatField(null=True, blank=True)
    dividend_payout = models.FloatField(null=True, blank=True)
    # Computed columns added during ETL
    net_profit_margin_pct = models.FloatField(null=True, blank=True)
    expense_ratio_pct = models.FloatField(null=True, blank=True)
    interest_coverage = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_profit_loss'
        unique_together = (('symbol', 'year'),)

    def __str__(self):
        return f"{self.symbol} — {self.year_id}"


class FactBalanceSheet(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    year = models.ForeignKey(DimYear, on_delete=models.DO_NOTHING, db_column='year_id', null=True)
    equity_capital = models.FloatField(null=True, blank=True)
    reserves = models.FloatField(null=True, blank=True)
    borrowings = models.FloatField(null=True, blank=True)
    other_liabilities = models.FloatField(null=True, blank=True)
    total_liabilities = models.FloatField(null=True, blank=True)
    fixed_assets = models.FloatField(null=True, blank=True)
    cwip = models.FloatField(null=True, blank=True)
    investments = models.FloatField(null=True, blank=True)
    other_assets = models.FloatField(db_column='other_asset', null=True, blank=True)
    total_assets = models.FloatField(null=True, blank=True)
    # Computed columns
    debt_to_equity = models.FloatField(null=True, blank=True)
    equity_ratio = models.FloatField(null=True, blank=True)


    class Meta:
        managed = False
        db_table = 'fact_balance_sheet'
        unique_together = (('symbol', 'year'),)

    def __str__(self):
        return f"{self.symbol} — {self.year_id}"


class FactCashFlow(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    year = models.ForeignKey(DimYear, on_delete=models.DO_NOTHING, db_column='year_id', null=True)
    operating_activity = models.FloatField(null=True, blank=True)
    investing_activity = models.FloatField(null=True, blank=True)
    financing_activity = models.FloatField(null=True, blank=True)
    net_cash_flow = models.FloatField(null=True, blank=True)
    # Computed columns
    free_cash_flow = models.FloatField(null=True, blank=True)


    class Meta:
        managed = False
        db_table = 'fact_cash_flow'
        unique_together = (('symbol', 'year'),)

    def __str__(self):
        return f"{self.symbol} — {self.year_id}"


class FactAnalysis(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    period_label = models.CharField(max_length=10)  # '10Y','5Y','3Y','TTM'
    compounded_sales_growth_pct = models.FloatField(null=True, blank=True)
    compounded_profit_growth_pct = models.FloatField(null=True, blank=True)
    stock_price_cagr_pct = models.FloatField(null=True, blank=True)
    roe_pct = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_analysis'

    def __str__(self):
        return f"{self.symbol} — {self.period_label}"


class FactMLScore(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        DimCompany, on_delete=models.DO_NOTHING, db_column='symbol',
        to_field='symbol', related_name='ml_scores'
    )
    computed_at = models.DateTimeField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    profitability_score = models.FloatField(null=True, blank=True)
    growth_score = models.FloatField(null=True, blank=True)
    leverage_score = models.FloatField(null=True, blank=True)
    cashflow_score = models.FloatField(null=True, blank=True)
    dividend_score = models.FloatField(null=True, blank=True)
    trend_score = models.FloatField(null=True, blank=True)
    health_label = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_ml_scores'

    @property
    def symbol(self):
        """Convenience accessor — Django stores the raw FK value as company_id."""
        return self.company_id

    def __str__(self):
        return f"{self.symbol} — {self.overall_score}"


class FactProsCons(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    is_pro = models.BooleanField()
    category = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=20, default='MANUAL')  # MANUAL or ML
    confidence = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_pros_cons'

    def __str__(self):
        return f"{self.symbol} — {'Pro' if self.is_pro else 'Con'}"


class FactDocument(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    year = models.IntegerField(null=True, blank=True)
    annual_report = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_documents'

    def __str__(self):
        return f"{self.symbol} — {self.year}"


class FactAnomaly(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    year = models.IntegerField(null=True, blank=True)
    metric = models.CharField(max_length=100, null=True, blank=True)
    z_score = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=20, null=True, blank=True)  # HIGH/MEDIUM/LOW
    detected_method = models.CharField(max_length=30, null=True, blank=True)  # ZSCORE/ISOLATION_FOREST
    is_reviewed = models.BooleanField(default=False)
    reviewer_notes = models.TextField(null=True, blank=True)
    detected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_anomalies'

    def __str__(self):
        return f"{self.symbol} — {self.metric} ({self.severity})"


class FactCluster(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    cluster_id = models.IntegerField(null=True, blank=True)
    cluster_label = models.CharField(max_length=200, null=True, blank=True)
    pca_x = models.FloatField(null=True, blank=True)
    pca_y = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'fact_clusters'

    def __str__(self):
        return f"{self.symbol} — Cluster {self.cluster_id}"
