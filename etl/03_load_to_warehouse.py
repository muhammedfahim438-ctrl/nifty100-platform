"""
ETL Script 03 — Load to Warehouse
====================================
Reads clean CSVs from data/clean/
Creates star schema tables in PostgreSQL
Loads data using upsert (ON CONFLICT DO UPDATE)
Runs 8 data quality checks after load

Run from project root:
    python etl/03_load_to_warehouse.py
"""

import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR    = PROJECT_ROOT / "data" / "clean"

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("DB_NAME",     "nifty100")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def get_engine():
    """Create and return a SQLAlchemy engine."""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return engine
    except Exception as e:
        logger.error(f"Could not connect to PostgreSQL: {e}")
        logger.error("Make sure Docker is running: docker-compose up -d")
        sys.exit(1)


# Each table is a separate string — no splitting needed
TABLES = [
    ("dim_sector", """
        CREATE TABLE IF NOT EXISTS dim_sector (
            sector_id   SERIAL PRIMARY KEY,
            sector_name VARCHAR(100) NOT NULL UNIQUE,
            sector_code VARCHAR(20)
        )
    """),
    ("dim_health_label", """
        CREATE TABLE IF NOT EXISTS dim_health_label (
            label_id   SERIAL PRIMARY KEY,
            label_name VARCHAR(20)  NOT NULL UNIQUE,
            min_score  NUMERIC(5,2) NOT NULL,
            max_score  NUMERIC(5,2) NOT NULL,
            color_hex  VARCHAR(10)  NOT NULL
        )
    """),
    ("dim_company", """
        CREATE TABLE IF NOT EXISTS dim_company (
            symbol        VARCHAR(20)  PRIMARY KEY,
            company_name  VARCHAR(200),
            sector_id     INT          REFERENCES dim_sector(sector_id),
            company_logo  TEXT,
            chart_link    TEXT,
            website       TEXT,
            nse_url       TEXT,
            bse_url       TEXT,
            face_value    NUMERIC(10,2),
            book_value    NUMERIC(10,2),
            roce_pct      NUMERIC(10,2),
            roe_pct       NUMERIC(10,2),
            about_company TEXT
        )
    """),
    ("dim_year", """
        CREATE TABLE IF NOT EXISTS dim_year (
            year_id      SERIAL PRIMARY KEY,
            year_label   VARCHAR(20) NOT NULL UNIQUE,
            fiscal_year  INT,
            quarter      VARCHAR(5),
            is_ttm       BOOLEAN DEFAULT FALSE,
            is_half_year BOOLEAN DEFAULT FALSE,
            sort_order   INT
        )
    """),
    ("fact_profit_loss", """
        CREATE TABLE IF NOT EXISTS fact_profit_loss (
            id                    SERIAL PRIMARY KEY,
            symbol                VARCHAR(20)  NOT NULL REFERENCES dim_company(symbol),
            year_id               INT          NOT NULL REFERENCES dim_year(year_id),
            sales                 NUMERIC(20,2),
            expenses              NUMERIC(20,2),
            operating_profit      NUMERIC(20,2),
            opm_pct               NUMERIC(10,2),
            other_income          NUMERIC(20,2),
            interest              NUMERIC(20,2),
            depreciation          NUMERIC(20,2),
            profit_before_tax     NUMERIC(20,2),
            tax_pct               NUMERIC(10,2),
            net_profit            NUMERIC(20,2),
            eps                   NUMERIC(10,2),
            dividend_payout       NUMERIC(10,2),
            net_profit_margin_pct NUMERIC(10,2),
            expense_ratio_pct     NUMERIC(10,2),
            interest_coverage     NUMERIC(10,2),
            UNIQUE (symbol, year_id)
        )
    """),
    ("fact_balance_sheet", """
        CREATE TABLE IF NOT EXISTS fact_balance_sheet (
            id                SERIAL PRIMARY KEY,
            symbol            VARCHAR(20)  NOT NULL REFERENCES dim_company(symbol),
            year_id           INT          NOT NULL REFERENCES dim_year(year_id),
            equity_capital    NUMERIC(20,2),
            reserves          NUMERIC(20,2),
            borrowings        NUMERIC(20,2),
            other_liabilities NUMERIC(20,2),
            total_liabilities NUMERIC(20,2),
            fixed_assets      NUMERIC(20,2),
            cwip              NUMERIC(20,2),
            investments       NUMERIC(20,2),
            other_asset       NUMERIC(20,2),
            total_assets      NUMERIC(20,2),
            debt_to_equity    NUMERIC(10,4),
            equity_ratio      NUMERIC(10,4),
            UNIQUE (symbol, year_id)
        )
    """),
    ("fact_cash_flow", """
        CREATE TABLE IF NOT EXISTS fact_cash_flow (
            id                 SERIAL PRIMARY KEY,
            symbol             VARCHAR(20)  NOT NULL REFERENCES dim_company(symbol),
            year_id            INT          NOT NULL REFERENCES dim_year(year_id),
            operating_activity NUMERIC(20,2),
            investing_activity NUMERIC(20,2),
            financing_activity NUMERIC(20,2),
            net_cash_flow      NUMERIC(20,2),
            free_cash_flow     NUMERIC(20,2),
            UNIQUE (symbol, year_id)
        )
    """),
    ("fact_analysis", """
        CREATE TABLE IF NOT EXISTS fact_analysis (
            id                           SERIAL PRIMARY KEY,
            symbol                       VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
            period_label                 VARCHAR(10) NOT NULL,
            compounded_sales_growth_pct  NUMERIC(10,2),
            compounded_profit_growth_pct NUMERIC(10,2),
            stock_price_cagr_pct         NUMERIC(10,2),
            roe_pct                      NUMERIC(10,2),
            UNIQUE (symbol, period_label)
        )
    """),
    ("fact_pros_cons", """
        CREATE TABLE IF NOT EXISTS fact_pros_cons (
            id     SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
            is_pro BOOLEAN     NOT NULL,
            text   TEXT        NOT NULL,
            source VARCHAR(20) DEFAULT 'MANUAL',
            UNIQUE (symbol, is_pro, text)
        )
    """),
    ("fact_documents", """
        CREATE TABLE IF NOT EXISTS fact_documents (
            id            SERIAL PRIMARY KEY,
            symbol        VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
            year          INT         NOT NULL,
            annual_report TEXT,
            UNIQUE (symbol, year)
        )
    """),
    ("fact_ml_scores", """
        CREATE TABLE IF NOT EXISTS fact_ml_scores (
            id                  SERIAL PRIMARY KEY,
            symbol              VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
            computed_at         TIMESTAMP   DEFAULT NOW(),
            overall_score       NUMERIC(5,2),
            profitability_score NUMERIC(5,2),
            growth_score        NUMERIC(5,2),
            leverage_score      NUMERIC(5,2),
            cashflow_score      NUMERIC(5,2),
            dividend_score      NUMERIC(5,2),
            trend_score         NUMERIC(5,2),
            health_label        VARCHAR(20)
        )
    """),
]


def create_all_tables(engine) -> None:
    """Create all tables one by one so errors are visible."""
    logger.info("Creating tables in PostgreSQL...")
    try:
        with engine.connect() as conn:
            for table_name, sql in TABLES:
                conn.execute(text(sql))
                logger.info(f"  Created: {table_name}")
        logger.info("All tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def load_dim_sector(engine) -> dict:
    """Load dim_sector and return {sector_name: sector_id} map."""
    logger.info("Loading dim_sector...")
    df = pd.read_csv(CLEAN_DIR / "sector_mapping.csv")
    sectors = df["sector"].dropna().unique().tolist()
    sector_map = {}
    with engine.connect() as conn:
        for sector_name in sorted(sectors):
            result = conn.execute(text("""
                INSERT INTO dim_sector (sector_name, sector_code)
                VALUES (:name, :code)
                ON CONFLICT (sector_name) DO UPDATE
                    SET sector_name = EXCLUDED.sector_name
                RETURNING sector_id
            """), {"name": sector_name, "code": sector_name[:10].upper()})
            sector_map[sector_name] = result.fetchone()[0]
            conn.commit()
    logger.info(f"dim_sector loaded: {len(sector_map)} sectors")
    return sector_map


def load_dim_health_label(engine) -> None:
    """Load the 5 health labels."""
    logger.info("Loading dim_health_label...")
    labels = [
        ("EXCELLENT", 85.0, 100.0, "#16a34a"),
        ("GOOD",      70.0,  84.9, "#65a30d"),
        ("AVERAGE",   50.0,  69.9, "#ca8a04"),
        ("WEAK",      35.0,  49.9, "#ea580c"),
        ("POOR",       0.0,  34.9, "#dc2626"),
    ]
    with engine.connect() as conn:
        for label_name, min_score, max_score, color_hex in labels:
            conn.execute(text("""
                INSERT INTO dim_health_label (label_name, min_score, max_score, color_hex)
                VALUES (:name, :min, :max, :color)
                ON CONFLICT (label_name) DO UPDATE
                    SET min_score = EXCLUDED.min_score,
                        max_score = EXCLUDED.max_score,
                        color_hex = EXCLUDED.color_hex
            """), {"name": label_name, "min": min_score, "max": max_score, "color": color_hex})
            conn.commit()
    logger.info("dim_health_label loaded: 5 labels")


def load_dim_company(engine, sector_map: dict) -> None:
    """Load dim_company from companies.csv."""
    logger.info("Loading dim_company...")
    df = pd.read_csv(CLEAN_DIR / "companies.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0
    with engine.connect() as conn:
        for _, row in df.iterrows():
            sector_id = sector_map.get(row.get("sector"))
            conn.execute(text("""
                INSERT INTO dim_company (
                    symbol, company_name, sector_id,
                    company_logo, chart_link, website,
                    nse_url, bse_url, face_value,
                    book_value, roce_pct, roe_pct, about_company
                ) VALUES (
                    :symbol, :company_name, :sector_id,
                    :company_logo, :chart_link, :website,
                    :nse_url, :bse_url, :face_value,
                    :book_value, :roce_pct, :roe_pct, :about_company
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    company_name  = EXCLUDED.company_name,
                    sector_id     = EXCLUDED.sector_id,
                    company_logo  = EXCLUDED.company_logo,
                    chart_link    = EXCLUDED.chart_link,
                    website       = EXCLUDED.website,
                    nse_url       = EXCLUDED.nse_url,
                    bse_url       = EXCLUDED.bse_url,
                    face_value    = EXCLUDED.face_value,
                    book_value    = EXCLUDED.book_value,
                    roce_pct      = EXCLUDED.roce_pct,
                    roe_pct       = EXCLUDED.roe_pct,
                    about_company = EXCLUDED.about_company
            """), {
                "symbol"       : row["id"],
                "company_name" : row.get("company_name"),
                "sector_id"    : sector_id,
                "company_logo" : row.get("company_logo"),
                "chart_link"   : row.get("chart_link"),
                "website"      : row.get("website"),
                "nse_url"      : row.get("nse_profile"),
                "bse_url"      : row.get("bse_profile"),
                "face_value"   : row.get("face_value"),
                "book_value"   : row.get("book_value"),
                "roce_pct"     : row.get("roce_percentage"),
                "roe_pct"      : row.get("roe_percentage"),
                "about_company": row.get("about_company"),
            })
            count += 1
            conn.commit()
    logger.info(f"dim_company loaded: {count} companies")


def load_dim_year(engine) -> dict:
    """Load dim_year and return {year_label: year_id} map."""
    logger.info("Loading dim_year...")
    year_rows = []
    for filename in ["balancesheet.csv", "cashflow.csv", "profitandloss.csv"]:
        df = pd.read_csv(CLEAN_DIR / filename, dtype=str)
        if "year_label" in df.columns:
            subset = df[["year_label", "fiscal_year", "quarter",
                         "is_ttm", "is_half_year", "sort_order"]].drop_duplicates()
            year_rows.append(subset)
    all_years = pd.concat(year_rows).drop_duplicates(subset=["year_label"])
    all_years = all_years.replace({np.nan: None})
    year_map = {}
    with engine.connect() as conn:
        for _, row in all_years.iterrows():
            label = row["year_label"]
            if not label or str(label) == "nan":
                continue
            # Clean up NaN and type issues
            fiscal_year = row["fiscal_year"]
            fiscal_year = None if (fiscal_year is None or str(fiscal_year) == "nan") else int(float(fiscal_year))

            quarter = row["quarter"]
            quarter = None if (quarter is None or str(quarter) == "nan") else str(quarter)

            sort_order = row["sort_order"]
            sort_order = None if (sort_order is None or str(sort_order) == "nan") else int(float(sort_order))

            result = conn.execute(text("""
                INSERT INTO dim_year (
                    year_label, fiscal_year, quarter,
                    is_ttm, is_half_year, sort_order
                ) VALUES (
                    :label, :fiscal_year, :quarter,
                    :is_ttm, :is_half_year, :sort_order
                )
                ON CONFLICT (year_label) DO UPDATE
                    SET fiscal_year  = EXCLUDED.fiscal_year,
                        quarter      = EXCLUDED.quarter,
                        is_ttm       = EXCLUDED.is_ttm,
                        is_half_year = EXCLUDED.is_half_year,
                        sort_order   = EXCLUDED.sort_order
                RETURNING year_id
            """), {
                "label"       : label,
                "fiscal_year" : fiscal_year,
                "quarter"     : quarter,
                "is_ttm"      : str(row["is_ttm"]).lower() == "true",
                "is_half_year": str(row["is_half_year"]).lower() == "true",
                "sort_order"  : sort_order,
            })
            year_map[label] = result.fetchone()[0]
            conn.commit()
    logger.info(f"dim_year loaded: {len(year_map)} year entries")
    return year_map


def load_fact_profit_loss(engine, year_map: dict) -> None:
    """Load fact_profit_loss from profitandloss.csv."""
    logger.info("Loading fact_profit_loss...")
    df = pd.read_csv(CLEAN_DIR / "profitandloss.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0
    skipped = 0

    # Get valid symbols from dim_company
    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}
    with engine.connect() as conn:
        for _, row in df.iterrows():
            year_id = year_map.get(str(row.get("year_label", "")))
            if not year_id:
                skipped += 1
                continue

            # Skip if company not in dim_company
            if row["company_id"] not in company_symbols:
                skipped += 1
                continue
            conn.execute(text("""
                INSERT INTO fact_profit_loss (
                    symbol, year_id, sales, expenses,
                    operating_profit, opm_pct, other_income,
                    interest, depreciation, profit_before_tax,
                    tax_pct, net_profit, eps, dividend_payout,
                    net_profit_margin_pct, expense_ratio_pct, interest_coverage
                ) VALUES (
                    :symbol, :year_id, :sales, :expenses,
                    :operating_profit, :opm_pct, :other_income,
                    :interest, :depreciation, :profit_before_tax,
                    :tax_pct, :net_profit, :eps, :dividend_payout,
                    :net_profit_margin_pct, :expense_ratio_pct, :interest_coverage
                )
                ON CONFLICT (symbol, year_id) DO UPDATE SET
                    sales                 = EXCLUDED.sales,
                    expenses              = EXCLUDED.expenses,
                    operating_profit      = EXCLUDED.operating_profit,
                    opm_pct               = EXCLUDED.opm_pct,
                    other_income          = EXCLUDED.other_income,
                    interest              = EXCLUDED.interest,
                    depreciation          = EXCLUDED.depreciation,
                    profit_before_tax     = EXCLUDED.profit_before_tax,
                    tax_pct               = EXCLUDED.tax_pct,
                    net_profit            = EXCLUDED.net_profit,
                    eps                   = EXCLUDED.eps,
                    dividend_payout       = EXCLUDED.dividend_payout,
                    net_profit_margin_pct = EXCLUDED.net_profit_margin_pct,
                    expense_ratio_pct     = EXCLUDED.expense_ratio_pct,
                    interest_coverage     = EXCLUDED.interest_coverage
            """), {
                "symbol"               : row["company_id"],
                "year_id"              : year_id,
                "sales"                : row.get("sales"),
                "expenses"             : row.get("expenses"),
                "operating_profit"     : row.get("operating_profit"),
                "opm_pct"              : row.get("opm_percentage"),
                "other_income"         : row.get("other_income"),
                "interest"             : row.get("interest"),
                "depreciation"         : row.get("depreciation"),
                "profit_before_tax"    : row.get("profit_before_tax"),
                "tax_pct"              : row.get("tax_percentage"),
                "net_profit"           : row.get("net_profit"),
                "eps"                  : row.get("eps"),
                "dividend_payout"      : row.get("dividend_payout"),
                "net_profit_margin_pct": row.get("net_profit_margin_pct"),
                "expense_ratio_pct"    : row.get("expense_ratio_pct"),
                "interest_coverage"    : row.get("interest_coverage"),
            })
            count += 1
            conn.commit()
    logger.info(f"fact_profit_loss loaded: {count} rows, {skipped} skipped")


def load_fact_balance_sheet(engine, year_map: dict) -> None:
    """Load fact_balance_sheet from balancesheet.csv."""
    logger.info("Loading fact_balance_sheet...")
    df = pd.read_csv(CLEAN_DIR / "balancesheet.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0
    skipped = 0

    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}
    with engine.connect() as conn:
        for _, row in df.iterrows():
            year_id = year_map.get(str(row.get("year_label", "")))
            if not year_id:
                skipped += 1
                continue
            if row["company_id"] not in company_symbols:
                skipped += 1
                continue
            conn.execute(text("""
                INSERT INTO fact_balance_sheet (
                    symbol, year_id, equity_capital, reserves,
                    borrowings, other_liabilities, total_liabilities,
                    fixed_assets, cwip, investments, other_asset,
                    total_assets, debt_to_equity, equity_ratio
                ) VALUES (
                    :symbol, :year_id, :equity_capital, :reserves,
                    :borrowings, :other_liabilities, :total_liabilities,
                    :fixed_assets, :cwip, :investments, :other_asset,
                    :total_assets, :debt_to_equity, :equity_ratio
                )
                ON CONFLICT (symbol, year_id) DO UPDATE SET
                    equity_capital    = EXCLUDED.equity_capital,
                    reserves          = EXCLUDED.reserves,
                    borrowings        = EXCLUDED.borrowings,
                    other_liabilities = EXCLUDED.other_liabilities,
                    total_liabilities = EXCLUDED.total_liabilities,
                    fixed_assets      = EXCLUDED.fixed_assets,
                    cwip              = EXCLUDED.cwip,
                    investments       = EXCLUDED.investments,
                    other_asset       = EXCLUDED.other_asset,
                    total_assets      = EXCLUDED.total_assets,
                    debt_to_equity    = EXCLUDED.debt_to_equity,
                    equity_ratio      = EXCLUDED.equity_ratio
            """), {
                "symbol"           : row["company_id"],
                "year_id"          : year_id,
                "equity_capital"   : row.get("equity_capital"),
                "reserves"         : row.get("reserves"),
                "borrowings"       : row.get("borrowings"),
                "other_liabilities": row.get("other_liabilities"),
                "total_liabilities": row.get("total_liabilities"),
                "fixed_assets"     : row.get("fixed_assets"),
                "cwip"             : row.get("cwip"),
                "investments"      : row.get("investments"),
                "other_asset"      : row.get("other_asset"),
                "total_assets"     : row.get("total_assets"),
                "debt_to_equity"   : row.get("debt_to_equity"),
                "equity_ratio"     : row.get("equity_ratio"),
            })
            count += 1
            conn.commit()
    logger.info(f"fact_balance_sheet loaded: {count} rows, {skipped} skipped")


def load_fact_cash_flow(engine, year_map: dict) -> None:
    """Load fact_cash_flow from cashflow.csv."""
    logger.info("Loading fact_cash_flow...")
    df = pd.read_csv(CLEAN_DIR / "cashflow.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0
    skipped = 0

    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}

    with engine.connect() as conn:
        for _, row in df.iterrows():
            symbol = row["company_id"]

            if symbol not in company_symbols:
                skipped += 1
                continue

            year_label = str(row.get("year_label", ""))
            year_id = year_map.get(year_label)
            if not year_id:
                skipped += 1
                continue

            conn.execute(text("""
                INSERT INTO fact_cash_flow (
                    symbol, year_id, operating_activity,
                    investing_activity, financing_activity,
                    net_cash_flow, free_cash_flow
                ) VALUES (
                    :symbol, :year_id, :operating_activity,
                    :investing_activity, :financing_activity,
                    :net_cash_flow, :free_cash_flow
                )
                ON CONFLICT (symbol, year_id) DO UPDATE SET
                    operating_activity = EXCLUDED.operating_activity,
                    investing_activity = EXCLUDED.investing_activity,
                    financing_activity = EXCLUDED.financing_activity,
                    net_cash_flow      = EXCLUDED.net_cash_flow,
                    free_cash_flow     = EXCLUDED.free_cash_flow
            """), {
                "symbol"            : symbol,
                "year_id"           : year_id,
                "operating_activity": row.get("operating_activity"),
                "investing_activity": row.get("investing_activity"),
                "financing_activity": row.get("financing_activity"),
                "net_cash_flow"     : row.get("net_cash_flow"),
                "free_cash_flow"    : row.get("free_cash_flow"),
            })
            count += 1
        conn.commit()
    logger.info(f"fact_cash_flow loaded: {count} rows, {skipped} skipped")


def load_fact_analysis(engine) -> None:
    """Load fact_analysis from analysis.csv."""
    logger.info("Loading fact_analysis...")
    df = pd.read_csv(CLEAN_DIR / "analysis.csv", dtype=str)   # FIX: was prosandcons.csv
    df = df.replace({np.nan: None})
    count = 0
    skipped = 0

    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}
    with engine.connect() as conn:
        for _, row in df.iterrows():
            if row["company_id"] not in company_symbols:
                continue
            if not row.get("period_label") or str(row.get("period_label")) == "None":
                continue
            conn.execute(text("""
                INSERT INTO fact_analysis (
                    symbol, period_label,
                    compounded_sales_growth_pct,
                    compounded_profit_growth_pct,
                    stock_price_cagr_pct, roe_pct
                ) VALUES (
                    :symbol, :period_label,
                    :sales_growth, :profit_growth,
                    :stock_cagr, :roe_pct
                )
                ON CONFLICT (symbol, period_label) DO UPDATE SET
                    compounded_sales_growth_pct  = EXCLUDED.compounded_sales_growth_pct,
                    compounded_profit_growth_pct = EXCLUDED.compounded_profit_growth_pct,
                    stock_price_cagr_pct         = EXCLUDED.stock_price_cagr_pct,
                    roe_pct                      = EXCLUDED.roe_pct
            """), {
                "symbol"       : row["company_id"],
                "period_label" : row.get("period_label"),
                "sales_growth" : row.get("compounded_sales_growth_pct"),
                "profit_growth": row.get("compounded_profit_growth_pct"),
                "stock_cagr"   : row.get("stock_price_cagr_pct"),
                "roe_pct"      : row.get("roe_pct"),
            })
            count += 1
            conn.commit()
    logger.info(f"fact_cash_flow loaded: {count} rows, {skipped} skipped (symbols not in dim_company are skipped)")


def load_fact_pros_cons(engine) -> None:
    """Load fact_pros_cons from prosandcons.csv."""
    logger.info("Loading fact_pros_cons...")
    df = pd.read_csv(CLEAN_DIR / "prosandcons.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0

    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}
    with engine.connect() as conn:
        for _, row in df.iterrows():
            symbol = row["company_id"]
            if symbol not in company_symbols:
                continue
            if row.get("pros") and str(row["pros"]) != "None":
                conn.execute(text("""
                    INSERT INTO fact_pros_cons (symbol, is_pro, text, source)
                    VALUES (:symbol, TRUE, :text, 'MANUAL')
                    ON CONFLICT (symbol, is_pro, text) DO NOTHING
                """), {"symbol": symbol, "text": row["pros"]})
                count += 1
            if row.get("cons") and str(row["cons"]) != "None":
                conn.execute(text("""
                    INSERT INTO fact_pros_cons (symbol, is_pro, text, source)
                    VALUES (:symbol, FALSE, :text, 'MANUAL')
                    ON CONFLICT (symbol, is_pro, text) DO NOTHING
                """), {"symbol": symbol, "text": row["cons"]})
                count += 1
                conn.commit()
    logger.info(f"fact_pros_cons loaded: {count} rows")


def load_fact_documents(engine) -> None:
    """Load fact_documents from documents.csv."""
    logger.info("Loading fact_documents...")
    df = pd.read_csv(CLEAN_DIR / "documents.csv", dtype=str)
    df = df.replace({np.nan: None})
    count = 0
    skipped = 0

    with engine.connect() as c:
        result = c.execute(text("SELECT symbol FROM dim_company"))
        company_symbols = {row[0] for row in result}
    with engine.connect() as conn:
        for _, row in df.iterrows():
            year = row.get("Year")
            if row["company_id"] not in company_symbols:
                skipped += 1
                continue
            if not year or str(year) == "None":
                skipped += 1
                continue
            conn.execute(text("""
                INSERT INTO fact_documents (symbol, year, annual_report)
                VALUES (:symbol, :year, :annual_report)
                ON CONFLICT (symbol, year) DO UPDATE SET
                    annual_report = EXCLUDED.annual_report
            """), {
                "symbol"       : row["company_id"],
                "year"         : int(float(year)),
                "annual_report": row.get("Annual_Report"),
            })
            count += 1
            conn.commit()
    logger.info(f"fact_documents loaded: {count} rows, {skipped} skipped")


def run_quality_checks(engine) -> None:
    """Run 8 data quality checks after loading."""
    logger.info("=" * 60)
    logger.info("Running data quality checks...")
    logger.info("=" * 60)
    checks = [
        ("Check 1 — dim_company row count",
         "SELECT COUNT(*) FROM dim_company",
         lambda n: n >= 90),
        ("Check 2 — dim_year row count",
         "SELECT COUNT(*) FROM dim_year",
         lambda n: n >= 10),
        ("Check 3 — fact_profit_loss row count",
         "SELECT COUNT(*) FROM fact_profit_loss",
         lambda n: n >= 1000),
        ("Check 4 — fact_balance_sheet row count",
         "SELECT COUNT(*) FROM fact_balance_sheet",
         lambda n: n >= 1000),
        ("Check 5 — fact_cash_flow row count",
         "SELECT COUNT(*) FROM fact_cash_flow",
         lambda n: n >= 1000),
        ("Check 6 — No NULL symbols in fact_profit_loss",
         "SELECT COUNT(*) FROM fact_profit_loss WHERE symbol IS NULL",
         lambda n: n == 0),
        ("Check 7 — dim_health_label has 5 rows",
         "SELECT COUNT(*) FROM dim_health_label",
         lambda n: n == 5),
        ("Check 8 — fact_analysis has data",
         "SELECT COUNT(*) FROM fact_analysis",
         lambda n: n >= 5),
    ]
    all_passed = True
    with engine.connect() as conn:
        for check_name, sql, condition in checks:
            value  = conn.execute(text(sql)).scalar()
            passed = condition(value)
            status = "PASS ✓" if passed else "FAIL ✗"
            logger.info(f"{status} | {check_name} → {value}")
            if not passed:
                all_passed = False
    logger.info("=" * 60)
    if all_passed:
        logger.info("All 8 quality checks PASSED")
    else:
        logger.warning("Some quality checks FAILED — review the data")
    logger.info("=" * 60)


def load_all() -> None:
    """Main function — runs the full warehouse load."""
    logger.info("=" * 60)
    logger.info("ETL Script 03 — Load to Warehouse — STARTED")
    logger.info("=" * 60)

    engine = get_engine()
    # Tables already created via docker — skip creation
    # create_all_tables(engine)
    logger.info("Skipping table creation — tables already exist")

    sector_map = load_dim_sector(engine)
    load_dim_health_label(engine)
    load_dim_company(engine, sector_map)
    year_map = load_dim_year(engine)

    load_fact_profit_loss(engine, year_map)
    load_fact_balance_sheet(engine, year_map)
    load_fact_cash_flow(engine, year_map)
    load_fact_analysis(engine)
    load_fact_pros_cons(engine)
    load_fact_documents(engine)

    run_quality_checks(engine)
    logger.info("ETL Script 03 — COMPLETED")


if __name__ == "__main__":
    load_all()