"""
ETL Script 02 — Clean and Transform
=====================================
Reads raw CSVs from data/raw/
Cleans and standardises all data
Computes derived metrics
Saves clean CSVs to data/clean/

Run from project root:
    python etl/02_clean_and_transform.py
"""

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Setup logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR    = PROJECT_ROOT / "data" / "clean"

# ─────────────────────────────────────────────
# Sector mapping for all 92 companies
# ─────────────────────────────────────────────
SECTOR_MAPPING = {
    # IT
    "TCS"          : "IT",
    "INFY"         : "IT",
    "WIPRO"        : "IT",
    "HCLTECH"      : "IT",
    "TECHM"        : "IT",
    "LTIM"         : "IT",
    "PERSISTENT"   : "IT",
    "COFORGE"      : "IT",
    # Banking
    "HDFCBANK"     : "Banking",
    "ICICIBANK"    : "Banking",
    "SBIN"         : "Banking",
    "AXISBANK"     : "Banking",
    "KOTAKBANK"    : "Banking",
    "INDUSINDBK"   : "Banking",
    "BANKBARODA"   : "Banking",
    "CANBK"        : "Banking",
    "UNIONBANK"    : "Banking",
    "PNB"          : "Banking",
    "FEDERALBNK"   : "Banking",
    "IDFCFIRSTB"   : "Banking",
    # NBFC / Finance
    "BAJFINANCE"   : "NBFC",
    "BAJAJFINSV"   : "NBFC",
    "CHOLAFIN"     : "NBFC",
    "MUTHOOTFIN"   : "NBFC",
    "SHRIRAMFIN"   : "NBFC",
    # Insurance
    "SBILIFE"      : "Insurance",
    "HDFCLIFE"     : "Insurance",
    "ICICIPRULI"   : "Insurance",
    "GICRE"        : "Insurance",
    "NIACL"        : "Insurance",
    # Energy / Oil & Gas
    "RELIANCE"     : "Energy",
    "ONGC"         : "Energy",
    "IOC"          : "Energy",
    "BPCL"         : "Energy",
    "ATGL"         : "Energy",
    "MGL"          : "Energy",
    "IGL"          : "Energy",
    # Power
    "ADANIPOWER"   : "Power",
    "ADANIGREEN"   : "Power",
    "ADANIENSOL"   : "Power",
    "NTPC"         : "Power",
    "POWERGRID"    : "Power",
    "TATAPOWER"    : "Power",
    # Ports & Infrastructure
    "ADANIPORTS"   : "Ports & Infrastructure",
    "ADANIENT"     : "Ports & Infrastructure",
    # Cement
    "AMBUJACEM"    : "Cement",
    "ACC"          : "Cement",
    "SHREECEM"     : "Cement",
    "ULTRACEMCO"   : "Cement",
    # Healthcare & Pharma
    "APOLLOHOSP"   : "Healthcare",
    "SUNPHARMA"    : "Pharma",
    "DRREDDY"      : "Pharma",
    "CIPLA"        : "Pharma",
    "DIVISLAB"     : "Pharma",
    "AUROPHARMA"   : "Pharma",
    "TORNTPHARM"   : "Pharma",
    "MANKIND"      : "Pharma",
    # Auto
    "BAJAJ-AUTO"   : "Auto",
    "MARUTI"       : "Auto",
    "TATAMOTORS"   : "Auto",
    "M&M"          : "Auto",
    "EICHERMOT"    : "Auto",
    "HEROMOTOCO"   : "Auto",
    "TVSMOTORS"    : "Auto",
    "BOSCHLTD"     : "Auto",
    # FMCG / Consumer Goods
    "HINDUNILVR"   : "FMCG",
    "ITC"          : "FMCG",
    "NESTLEIND"    : "FMCG",
    "BRITANNIA"    : "FMCG",
    "DABUR"        : "FMCG",
    "MARICO"       : "FMCG",
    "COLPAL"       : "FMCG",
    "GODREJCP"     : "FMCG",
    "TATACONSUM"   : "FMCG",
    "VBL"          : "FMCG",
    # Paints
    "ASIANPAINT"   : "Paints",
    "BERGEPAINT"   : "Paints",
    # Telecom
    "BHARTIARTL"   : "Telecom",
    # Metals & Mining
    "TATASTEEL"    : "Metals",
    "JSWSTEEL"     : "Metals",
    "HINDALCO"     : "Metals",
    "VEDL"         : "Metals",
    "COALINDIA"    : "Metals",
    "NMDC"         : "Metals",
    # Capital Goods / Industrial
    "LT"           : "Capital Goods",
    "ABB"          : "Capital Goods",
    "SIEMENS"      : "Capital Goods",
    "HAVELLS"      : "Capital Goods",
    "BEL"          : "Capital Goods",
    "BHEL"         : "Capital Goods",
    # Holding Companies
    "BAJAJHLDNG"   : "Holding Company",
    # Real Estate
    "DLF"          : "Real Estate",
    "LODHA"        : "Real Estate",
    # Retail
    "DMART"        : "Retail",
    "TRENT"        : "Retail",
    # Others
    "ZOMATO"       : "Internet & Consumer",
    "NYKAA"        : "Internet & Consumer",
    "PAYTM"        : "Internet & Consumer",
    "LTF"          : "NBFC",
    "JIOFIN"       : "NBFC",
    "JIOFIN"       : "NBFC",
    # Additional companies
    "GAIL"         : "Energy",
    "GRASIM"       : "Capital Goods",
    "HAL"          : "Capital Goods",
    "ICICIGI"      : "Insurance",
    "INDIGO"       : "Aviation",
    "IRCTC"        : "Railways",
    "IRFC"         : "Railways",
    "JINDALSTEL"   : "Metals",
    "JSWENERGY"    : "Power",
    "LICI"         : "Insurance",
    "MOTHERSON"    : "Auto",
    "NAUKRI"       : "Internet & Consumer",
    "NHPC"         : "Power",
    "PFC"          : "NBFC",
    "PIDILITIND"   : "Chemicals",
    "RECLTD"       : "NBFC",
    "TITAN"        : "Consumer Goods",
    "TVSMOTOR"     : "Auto",
}



# ─────────────────────────────────────────────
# YEAR STANDARDISATION
# ─────────────────────────────────────────────

# Month abbreviation map — handles inconsistent capitalisation
MONTH_MAP = {
    "jan": "Jan", "feb": "Feb", "mar": "Mar",
    "apr": "Apr", "may": "May", "jun": "Jun",
    "jul": "Jul", "aug": "Aug", "sep": "Sep",
    "oct": "Oct", "nov": "Nov", "dec": "Dec",
}

# Which fiscal quarter each month belongs to
MONTH_TO_QUARTER = {
    "Jan": "Q3", "Feb": "Q3", "Mar": "Q4",
    "Apr": "Q1", "May": "Q1", "Jun": "Q1",
    "Jul": "Q2", "Aug": "Q2", "Sep": "Q2",
    "Oct": "Q3", "Nov": "Q3", "Dec": "Q3",
}

# Sort order base per month (so Mar 2024 sorts after Dec 2023)
MONTH_SORT_BASE = {
    "Apr": 1,  "May": 2,  "Jun": 3,
    "Jul": 4,  "Aug": 5,  "Sep": 6,
    "Oct": 7,  "Nov": 8,  "Dec": 9,
    "Jan": 10, "Feb": 11, "Mar": 12,
}


def standardise_year(raw: str) -> dict:
    """
    Convert any year string to a standard format.

    Handles:
        'Mar 2024'    → already correct
        'Mar-24'      → Mar 2024
        'Mar-2024'    → Mar 2024
        'TTM'         → TTM
        '2024'        → Mar 2024 (plain year = fiscal year end)
        '2024.5'      → Sep 2024 (half year)
        'Mar 2023 15' → Mar 2023 (strip trailing noise)
        'Mar 2016 9m' → Mar 2016 (strip trailing noise)
    """
    if not isinstance(raw, str):
        raw = str(raw)

    raw = raw.strip()

    # ── TTM / 1 Year / Last Year ──
    if raw.upper() in ("TTM", "1 YEAR", "LAST YEAR", "1YEAR"):
        return {
            "year_label"  : "TTM",
            "fiscal_year" : None,
            "quarter"     : None,
            "is_ttm"      : True,
            "is_half_year": False,
            "sort_order"  : 999999,
        }

    # ── Plain integer year e.g. '2024' → 'Mar 2024' ──
    match_int = re.match(r"^(\d{4})$", raw)
    if match_int:
        year = int(match_int.group(1))
        return _build_year_dict("Mar", year)

    # ── Half year e.g. '2024.5' → 'Sep 2024' ──
    match_half = re.match(r"^(\d{4})\.5$", raw)
    if match_half:
        year = int(match_half.group(1))
        result = _build_year_dict("Sep", year)
        result["is_half_year"] = True
        return result

    # ── Strip trailing noise e.g. 'Mar 2023 15' or 'Mar 2016 9m' ──
    raw_clean = re.sub(r"(\b[A-Za-z]{3}\s+\d{4})\s+.*$", r"\1", raw).strip()

    # ── Format: 'Mar-24' or 'Mar-2024' ──
    match_short = re.match(r"^([A-Za-z]{3})[-](\d{2}|\d{4})$", raw_clean)
    if match_short:
        mon_raw = match_short.group(1).lower()
        yr_raw  = match_short.group(2)
        mon     = MONTH_MAP.get(mon_raw)
        if mon:
            year = int(yr_raw) if len(yr_raw) == 4 else 2000 + int(yr_raw)
            return _build_year_dict(mon, year)

    # ── Format: 'Mar 2024' ──
    match_long = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", raw_clean)
    if match_long:
        mon_raw = match_long.group(1).lower()
        year    = int(match_long.group(2))
        mon     = MONTH_MAP.get(mon_raw)
        if mon:
            return _build_year_dict(mon, year)

    # ── Unknown format ──
    logger.warning(f"Could not parse year value: '{raw}'")
    return {
        "year_label"  : raw,
        "fiscal_year" : None,
        "quarter"     : None,
        "is_ttm"      : False,
        "is_half_year": False,
        "sort_order"  : 0,
    }

def _build_year_dict(mon: str, year: int) -> dict:
    """
    Build the full year dictionary given a clean month and year.

    Args:
        mon  : 3-letter month e.g. 'Mar'
        year : 4-digit year e.g. 2024
    """
    quarter     = MONTH_TO_QUARTER.get(mon, "Q4")
    month_base  = MONTH_SORT_BASE.get(mon, 0)
    sort_order  = year * 100 + month_base

    return {
        "year_label"  : f"{mon} {year}",
        "fiscal_year" : year,
        "quarter"     : quarter,
        "is_ttm"      : False,
        "is_half_year": False,
        "sort_order"  : sort_order,
    }


def add_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply year standardisation to a DataFrame that has a 'year' column.
    Adds: year_label, fiscal_year, quarter, is_ttm, is_half_year, sort_order.

    Args:
        df: DataFrame with a 'year' column

    Returns:
        DataFrame with new year columns added
    """
    year_data = df["year"].apply(standardise_year).apply(pd.Series)
    df = pd.concat([df, year_data], axis=1)
    return df


# ─────────────────────────────────────────────
# ANALYSIS TABLE — parse growth strings
# ─────────────────────────────────────────────

# Maps the text labels in the data to short period codes
PERIOD_MAP = {
    "10 years" : "10Y",
    "10years"  : "10Y",
    "5 years"  : "5Y",
    "5years"   : "5Y",
    "3 years"  : "3Y",
    "3years"   : "3Y",
    "ttm"      : "TTM",
    "1 year"   : "TTM",
    "last year": "TTM",
}


def parse_growth_string(value: str) -> tuple:
    """
    Parse a string like '10 Years: 21%' into ('10Y', 21.0).
    Also handles 'TTM: 43%', '1 Year: 13%', 'Last Year: 17%'.

    Args:
        value: Raw string from the analysis table

    Returns:
        Tuple of (period_label, numeric_value)
        e.g. ('10Y', 21.0) or ('TTM', 43.0)
    """
    if not isinstance(value, str) or pd.isna(value):
        return (None, None)

    value = value.strip()

    # Match pattern: "Label: XX%" or "Label:XX%"
    match = re.match(
        r"^(.+?)[:\s]+\s*([-\d.]+)%?$", value, re.IGNORECASE
    
    )
    if not match:
        logger.warning(f"Could not parse growth string: '{value}'")
        return (None, None)

    label_raw   = match.group(1).strip().lower()
    number_raw  = match.group(2).strip()

    period = PERIOD_MAP.get(label_raw)
    if not period:
        logger.warning(f"Unknown period label: '{label_raw}'")
        period = label_raw.upper()

    try:
        value_pct = float(number_raw)
    except ValueError:
        logger.warning(f"Could not convert to float: '{number_raw}'")
        value_pct = None

    return (period, value_pct)


def clean_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the analysis table.
    Parses all 4 growth columns and adds period_label column.

    Args:
        df: Raw analysis DataFrame

    Returns:
        Cleaned DataFrame with numeric values and period labels
    """
    logger.info("Cleaning analysis table...")

    growth_cols = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    # Parse period from the first non-null growth column
    df["period_label"] = None

    for col in growth_cols:
        parsed = df[col].apply(parse_growth_string)
        df[f"{col}_period"] = parsed.apply(lambda x: x[0])
        df[f"{col}_pct"]    = parsed.apply(lambda x: x[1])

        # Fill period_label from first available column
        mask = df["period_label"].isna() & df[f"{col}_period"].notna()
        df.loc[mask, "period_label"] = df.loc[mask, f"{col}_period"]

    # Drop the original string columns and the per-column period columns
    cols_to_drop = growth_cols + [f"{c}_period" for c in growth_cols]
    df = df.drop(columns=cols_to_drop)

    logger.info(f"Analysis table cleaned: {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# NUMERIC CONVERSION
# ─────────────────────────────────────────────

def to_numeric_safe(series: pd.Series) -> pd.Series:
    """
    Convert a Series to numeric, turning errors into NaN.
    Handles strings like '1,234.56' by removing commas first.

    Args:
        series: pandas Series to convert

    Returns:
        Numeric Series
    """
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )


# ─────────────────────────────────────────────
# COMPUTED COLUMNS
# ─────────────────────────────────────────────

def compute_balance_sheet_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed columns to the balance sheet table.

    Computes:
        debt_to_equity  = borrowings / (equity_capital + reserves)
        equity_ratio    = (equity_capital + reserves) / total_assets

    Args:
        df: Clean balance sheet DataFrame

    Returns:
        DataFrame with new computed columns
    """
    logger.info("Computing balance sheet metrics...")

    num_cols = [
        "equity_capital", "reserves", "borrowings",
        "other_liabilities", "total_liabilities",
        "fixed_assets", "cwip", "investments",
        "other_asset", "total_assets"
    ]
    for col in num_cols:
        df[col] = to_numeric_safe(df[col])

    equity = df["equity_capital"] + df["reserves"]

    # Avoid division by zero
    df["debt_to_equity"] = np.where(
        equity != 0,
        df["borrowings"] / equity,
        np.nan
    )

    df["equity_ratio"] = np.where(
        df["total_assets"] != 0,
        equity / df["total_assets"],
        np.nan
    )

    return df


def compute_profit_loss_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed columns to the profit and loss table.

    Computes:
        net_profit_margin_pct = (net_profit / sales) * 100
        expense_ratio_pct     = (expenses / sales) * 100
        interest_coverage     = operating_profit / interest

    Args:
        df: Clean profit and loss DataFrame

    Returns:
        DataFrame with new computed columns
    """
    logger.info("Computing profit & loss metrics...")

    num_cols = [
        "sales", "expenses", "operating_profit",
        "other_income", "interest", "depreciation",
        "profit_before_tax", "net_profit", "eps", "dividend_payout"
    ]
    for col in num_cols:
        df[col] = to_numeric_safe(df[col])

    df["net_profit_margin_pct"] = np.where(
        df["sales"] != 0,
        (df["net_profit"] / df["sales"]) * 100,
        np.nan
    )

    df["expense_ratio_pct"] = np.where(
        df["sales"] != 0,
        (df["expenses"] / df["sales"]) * 100,
        np.nan
    )

    df["interest_coverage"] = np.where(
        df["interest"] != 0,
        df["operating_profit"] / df["interest"],
        np.nan
    )

    return df


def compute_cash_flow_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed columns to the cash flow table.

    Computes:
        free_cash_flow = operating_activity + investing_activity

    Args:
        df: Clean cash flow DataFrame

    Returns:
        DataFrame with new computed columns
    """
    logger.info("Computing cash flow metrics...")

    num_cols = [
        "operating_activity", "investing_activity",
        "financing_activity", "net_cash_flow"
    ]
    for col in num_cols:
        df[col] = to_numeric_safe(df[col])

    df["free_cash_flow"] = (
        df["operating_activity"] + df["investing_activity"]
    )

    return df


# ─────────────────────────────────────────────
# SECTOR MAPPING
# ─────────────────────────────────────────────

def add_sector(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'sector' column to the companies DataFrame
    using the SECTOR_MAPPING dictionary.

    Args:
        df: Companies DataFrame with 'id' as symbol

    Returns:
        DataFrame with 'sector' column added
    """
    df["sector"] = df["id"].map(SECTOR_MAPPING)

    unmapped = df[df["sector"].isna()]["id"].tolist()
    if unmapped:
        logger.warning(f"Companies with no sector mapping: {unmapped}")

    return df


# ─────────────────────────────────────────────
# INDIVIDUAL TABLE CLEANERS
# ─────────────────────────────────────────────

def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the companies master table."""
    logger.info("Cleaning companies table...")

    # Strip whitespace from text columns
    text_cols = ["company_name", "about_company", "website"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Convert numeric columns
    df["face_value"]      = to_numeric_safe(df["face_value"])
    df["book_value"]      = to_numeric_safe(df["book_value"])
    df["roce_percentage"] = to_numeric_safe(df["roce_percentage"])
    df["roe_percentage"]  = to_numeric_safe(df["roe_percentage"])

    # Add sector
    df = add_sector(df)

    logger.info(f"Companies table cleaned: {len(df)} rows")
    return df


def clean_balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the balance sheet table."""
    logger.info("Cleaning balance sheet table...")

    df = add_year_columns(df)
    df = compute_balance_sheet_metrics(df)

    logger.info(f"Balance sheet cleaned: {len(df)} rows")
    return df


def clean_cash_flow(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the cash flow table."""
    logger.info("Cleaning cash flow table...")

    df = add_year_columns(df)
    df = compute_cash_flow_metrics(df)

    logger.info(f"Cash flow cleaned: {len(df)} rows")
    return df


def clean_profit_loss(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the profit and loss table."""
    logger.info("Cleaning profit & loss table...")

    df = add_year_columns(df)
    df = compute_profit_loss_metrics(df)

    logger.info(f"Profit & loss cleaned: {len(df)} rows")
    return df


def clean_documents(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the documents table."""
    logger.info("Cleaning documents table...")

    # Year column is already integer in this file — just ensure it's int
    df["Year"] = to_numeric_safe(df["Year"]).astype("Int64")

    logger.info(f"Documents cleaned: {len(df)} rows")
    return df


def clean_pros_cons(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the pros and cons table."""
    logger.info("Cleaning pros & cons table...")

    # Strip whitespace
    for col in ["pros", "cons"]:
        df[col] = df[col].astype(str).str.strip()
        # Convert 'nan' strings back to real NaN
        df[col] = df[col].replace("nan", np.nan)

    logger.info(f"Pros & cons cleaned: {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# SAVE SECTOR MAPPING
# ─────────────────────────────────────────────

def save_sector_mapping() -> None:
    """
    Save the sector mapping as a standalone CSV.
    Used later when building dim_sector in the warehouse.
    """
    rows = [
        {"symbol": symbol, "sector": sector}
        for symbol, sector in SECTOR_MAPPING.items()
    ]
    df = pd.DataFrame(rows)
    output_path = CLEAN_DIR / "sector_mapping.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Sector mapping saved → {output_path} ({len(df)} companies)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def clean_all() -> None:
    """
    Main function — reads all raw CSVs, cleans them,
    and saves to data/clean/.
    """
    logger.info("=" * 60)
    logger.info("ETL Script 02 — Clean and Transform — STARTED")
    logger.info("=" * 60)

    # Create output directory
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {CLEAN_DIR}")

    # ── Load all raw CSVs ──
    logger.info("Loading raw CSVs...")
    df_analysis   = pd.read_csv(RAW_DIR / "analysis.csv",      dtype=str)
    df_proscons   = pd.read_csv(RAW_DIR / "prosandcons.csv",   dtype=str)
    df_balance    = pd.read_csv(RAW_DIR / "balancesheet.csv",  dtype=str)
    df_cashflow   = pd.read_csv(RAW_DIR / "cashflow.csv",      dtype=str)
    df_companies  = pd.read_csv(RAW_DIR / "companies.csv",     dtype=str)
    df_pl         = pd.read_csv(RAW_DIR / "profitandloss.csv", dtype=str)
    df_documents  = pd.read_csv(RAW_DIR / "documents.csv",     dtype=str)

    # Replace any remaining NULL strings with NaN
    null_strings = ["NULL", "Null", "null", "None", "NA", "N/A"]
    for df in [df_analysis, df_proscons, df_balance, df_cashflow,
               df_companies, df_pl, df_documents]:
        df.replace(null_strings, np.nan, inplace=True)

    # ── Clean each table ──
    df_analysis  = clean_analysis(df_analysis)
    df_proscons  = clean_pros_cons(df_proscons)
    df_balance   = clean_balance_sheet(df_balance)
    df_cashflow  = clean_cash_flow(df_cashflow)
    df_companies = clean_companies(df_companies)
    df_pl        = clean_profit_loss(df_pl)
    df_documents = clean_documents(df_documents)

    # ── Save all clean CSVs ──
    outputs = [
        (df_analysis,  "analysis.csv"),
        (df_proscons,  "prosandcons.csv"),
        (df_balance,   "balancesheet.csv"),
        (df_cashflow,  "cashflow.csv"),
        (df_companies, "companies.csv"),
        (df_pl,        "profitandloss.csv"),
        (df_documents, "documents.csv"),
    ]

    for df, filename in outputs:
        path = CLEAN_DIR / filename
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info(f"Saved → {path}  ({len(df)} rows, {len(df.columns)} columns)")

    # ── Save sector mapping ──
    save_sector_mapping()

    logger.info("=" * 60)
    logger.info("ETL Script 02 — COMPLETED")
    logger.info(f"Clean CSVs saved to: {CLEAN_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    clean_all()