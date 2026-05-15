"""
Models for the Nifty 100 Financial Intelligence Platform.
These models map to the existing PostgreSQL star schema tables.
We use managed=False so Django reads but does not modify the tables.
"""

from django.db import models


class DimSector(models.Model):
    """Sector dimension table."""
    sector_id   = models.AutoField(primary_key=True)
    sector_name = models.CharField(max_length=100, unique=True)
    sector_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed  = False
        db_table = "dim_sector"

    def __str__(self):
        return self.sector_name


class DimCompany(models.Model):
    """Company dimension table."""
    symbol        = models.CharField(max_length=20, primary_key=True)
    company_name  = models.CharField(max_length=200, blank=True, null=True)
    sector        = models.ForeignKey(
                        DimSector,
                        on_delete=models.SET_NULL,
                        null=True,
                        db_column="sector_id"
                    )
    company_logo  = models.TextField(blank=True, null=True)
    chart_link    = models.TextField(blank=True, null=True)
    website       = models.TextField(blank=True, null=True)
    nse_url       = models.TextField(blank=True, null=True)
    bse_url       = models.TextField(blank=True, null=True)
    face_value    = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    book_value    = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    roce_pct      = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    roe_pct       = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    about_company = models.TextField(blank=True, null=True)

    class Meta:
        managed  = False
        db_table = "dim_company"

    def __str__(self):
        return f"{self.symbol} — {self.company_name}"


class DimYear(models.Model):
    """Year dimension table."""
    year_id      = models.AutoField(primary_key=True)
    year_label   = models.CharField(max_length=20, unique=True)
    fiscal_year  = models.IntegerField(null=True)
    quarter      = models.CharField(max_length=5, null=True)
    is_ttm       = models.BooleanField(default=False)
    is_half_year = models.BooleanField(default=False)
    sort_order   = models.IntegerField(null=True)

    class Meta:
        managed  = False
        db_table = "dim_year"

    def __str__(self):
        return self.year_label


class DimHealthLabel(models.Model):
    """Health label dimension table."""
    label_id   = models.AutoField(primary_key=True)
    label_name = models.CharField(max_length=20, unique=True)
    min_score  = models.DecimalField(max_digits=5, decimal_places=2)
    max_score  = models.DecimalField(max_digits=5, decimal_places=2)
    color_hex  = models.CharField(max_length=10)

    class Meta:
        managed  = False
        db_table = "dim_health_label"

    def __str__(self):
        return self.label_name


class FactProfitLoss(models.Model):
    """Profit and loss fact table."""
    id                    = models.AutoField(primary_key=True)
    symbol                = models.ForeignKey(
                                DimCompany,
                                on_delete=models.CASCADE,
                                db_column="symbol"
                            )
    year                  = models.ForeignKey(
                                DimYear,
                                on_delete=models.CASCADE,
                                db_column="year_id"
                            )
    sales                 = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    expenses              = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    operating_profit      = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    opm_pct               = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    other_income          = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    interest              = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    depreciation          = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    profit_before_tax     = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    tax_pct               = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    net_profit            = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    eps                   = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    dividend_payout       = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    net_profit_margin_pct = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    expense_ratio_pct     = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    interest_coverage     = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        managed  = False
        db_table = "fact_profit_loss"

    def __str__(self):
        return f"{self.symbol_id} — {self.year_id}"


class FactBalanceSheet(models.Model):
    """Balance sheet fact table."""
    id                = models.AutoField(primary_key=True)
    symbol            = models.ForeignKey(
                            DimCompany,
                            on_delete=models.CASCADE,
                            db_column="symbol"
                        )
    year              = models.ForeignKey(
                            DimYear,
                            on_delete=models.CASCADE,
                            db_column="year_id"
                        )
    equity_capital    = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    reserves          = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    borrowings        = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    other_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    total_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    fixed_assets      = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    cwip              = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    investments       = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    other_asset       = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    total_assets      = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    debt_to_equity    = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    equity_ratio      = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        managed  = False
        db_table = "fact_balance_sheet"


class FactCashFlow(models.Model):
    """Cash flow fact table."""
    id                 = models.AutoField(primary_key=True)
    symbol             = models.ForeignKey(
                             DimCompany,
                             on_delete=models.CASCADE,
                             db_column="symbol"
                         )
    year               = models.ForeignKey(
                             DimYear,
                             on_delete=models.CASCADE,
                             db_column="year_id"
                         )
    operating_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    investing_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    financing_activity = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    net_cash_flow      = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    free_cash_flow     = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    class Meta:
        managed  = False
        db_table = "fact_cash_flow"


class FactMLScore(models.Model):
    """ML health scores fact table."""
    id                  = models.AutoField(primary_key=True)
    symbol              = models.ForeignKey(
                              DimCompany,
                              on_delete=models.CASCADE,
                              db_column="symbol"
                          )
    computed_at         = models.DateTimeField(auto_now_add=True)
    overall_score       = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    profitability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    growth_score        = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    leverage_score      = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    cashflow_score      = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    dividend_score      = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    trend_score         = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    health_label        = models.CharField(max_length=20, null=True)

    class Meta:
        managed  = False
        db_table = "fact_ml_scores"

    def __str__(self):
        return f"{self.symbol_id} — {self.health_label} ({self.overall_score})"


class FactProsCons(models.Model):
    """Pros and cons fact table."""
    id     = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(
                 DimCompany,
                 on_delete=models.CASCADE,
                 db_column="symbol"
             )
    is_pro = models.BooleanField()
    text   = models.TextField()
    source = models.CharField(max_length=20, default="MANUAL")

    class Meta:
        managed  = False
        db_table = "fact_pros_cons"


class FactDocument(models.Model):
    """Documents fact table."""
    id            = models.AutoField(primary_key=True)
    symbol        = models.ForeignKey(
                        DimCompany,
                        on_delete=models.CASCADE,
                        db_column="symbol"
                    )
    year          = models.IntegerField()
    annual_report = models.TextField(null=True)

    class Meta:
        managed  = False
        db_table = "fact_documents"