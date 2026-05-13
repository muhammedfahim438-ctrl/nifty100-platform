"""
ETL Script 01 — Extract from Excel
====================================
Reads all 7 source Excel files from data/source/
Validates columns and row counts
Saves each table as a clean CSV to data/raw/

Run from project root:
    python etl/01_extract_from_excel.py
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Setup logging — writes to console with timestamp
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Load environment variables from .env file
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# Define all paths relative to project root
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR   = PROJECT_ROOT / "data" / "source"
RAW_DIR      = PROJECT_ROOT / "data" / "raw"

# ─────────────────────────────────────────────
# File config — filename, sheet name, expected columns
# ─────────────────────────────────────────────
FILES = [
    {
        "filename"  : "analysis.xlsx",
        "sheet"     : "Analysis",
        "output"    : "analysis.csv",
        "expected_columns": [
            "id", "company_id", "compounded_sales_growth",
            "compounded_profit_growth", "stock_price_cagr", "roe"
        ],
    },
    {
        "filename"  : "prosandcons.xlsx",
        "sheet"     : "Pros & Cons",
        "output"    : "prosandcons.csv",
        "expected_columns": [
            "id", "company_id", "pros", "cons"
        ],
    },
    {
        "filename"  : "balancesheet.xlsx",
        "sheet"     : "Balance Sheet",
        "output"    : "balancesheet.csv",
        "expected_columns": [
            "id", "company_id", "year", "equity_capital", "reserves",
            "borrowings", "other_liabilities", "total_liabilities",
            "fixed_assets", "cwip", "investments", "other_asset",
            "total_assets"
        ],
    },
    {
        "filename"  : "cashflow.xlsx",
        "sheet"     : "Cash Flow",
        "output"    : "cashflow.csv",
        "expected_columns": [
            "id", "company_id", "year", "operating_activity",
            "investing_activity", "financing_activity", "net_cash_flow"
        ],
    },
    {
        "filename"  : "companies.xlsx",
        "sheet"     : "Companies",
        "output"    : "companies.csv",
        "expected_columns": [
            "id", "company_logo", "company_name", "chart_link",
            "about_company", "website", "nse_profile", "bse_profile",
            "face_value", "book_value", "roce_percentage", "roe_percentage"
        ],
    },
    {
        "filename"  : "profitandloss.xlsx",
        "sheet"     : "Profit & Loss",
        "output"    : "profitandloss.csv",
        "expected_columns": [
            "id", "company_id", "year", "sales", "expenses",
            "operating_profit", "opm_percentage", "other_income",
            "interest", "depreciation", "profit_before_tax",
            "tax_percentage", "net_profit", "eps", "dividend_payout"
        ],
    },
    {
        "filename"  : "documents.xlsx",
        "sheet"     : "Documents",
        "output"    : "documents.csv",
        "expected_columns": [
            "id", "company_id", "Year", "Annual_Report"
        ],
    },
]

# ─────────────────────────────────────────────
# NULL string values to treat as real NaN
# ─────────────────────────────────────────────
NULL_VALUES = ["NULL", "Null", "null", "NA", "N/A", "None", ""]


def ensure_output_dir() -> None:
    """Create data/raw/ directory if it does not exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {RAW_DIR}")


def read_excel_file(filename: str, sheet: str) -> pd.DataFrame:
    """
    Read one Excel file into a pandas DataFrame.

    Args:
        filename: Name of the Excel file (e.g. 'analysis.xlsx')
        sheet:    Exact sheet name inside the file

    Returns:
        DataFrame with raw data from the sheet
    """
    filepath = SOURCE_DIR / filename

    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    logger.info(f"Reading {filename} → sheet '{sheet}'")

    df = pd.read_excel(
        filepath,
        sheet_name=sheet,
        header=1,                 # row 1 is a title, row 2 has real column names
        na_values=NULL_VALUES,    # treat these strings as NaN
        keep_default_na=True,     # also keep pandas default NaN detection
        dtype=str,                # read everything as string first
                                  # we will cast types in script 02
    )

    return df


def validate_columns(df: pd.DataFrame, expected: list, filename: str) -> None:
    """
    Check that all expected columns exist in the DataFrame.
    Extra columns are allowed — we just warn about them.

    Args:
        df:       DataFrame to check
        expected: List of column names we require
        filename: Used only for logging
    """
    actual   = list(df.columns)
    missing  = [c for c in expected if c not in actual]
    extra    = [c for c in actual   if c not in expected]

    if missing:
        logger.error(f"{filename}: MISSING columns: {missing}")
        logger.error(f"{filename}: Actual columns are: {actual}")
        sys.exit(1)

    if extra:
        logger.warning(f"{filename}: Extra columns found (keeping them): {extra}")


def save_csv(df: pd.DataFrame, output_filename: str) -> None:
    """
    Save DataFrame to data/raw/ as a CSV file.

    Args:
        df:              DataFrame to save
        output_filename: Name of the output CSV file
    """
    output_path = RAW_DIR / output_filename
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved → {output_path}  ({len(df)} rows, {len(df.columns)} columns)")


def print_summary(df: pd.DataFrame, filename: str) -> None:
    """
    Print a quick summary of the extracted DataFrame.

    Args:
        df:       DataFrame to summarise
        filename: Used only for display
    """
    logger.info(f"{'─'*50}")
    logger.info(f"File     : {filename}")
    logger.info(f"Rows     : {len(df)}")
    logger.info(f"Columns  : {list(df.columns)}")

    # Count how many cells are NaN
    null_count = df.isna().sum().sum()
    logger.info(f"NaN cells: {null_count}")
    logger.info(f"{'─'*50}")


def extract_all() -> None:
    """
    Main function — loops through all 7 files,
    reads, validates, prints summary, and saves CSV.
    """
    logger.info("=" * 60)
    logger.info("ETL Script 01 — Extract from Excel — STARTED")
    logger.info("=" * 60)

    ensure_output_dir()

    success_count = 0

    for file_config in FILES:
        filename = file_config["filename"]
        sheet    = file_config["sheet"]
        output   = file_config["output"]
        expected = file_config["expected_columns"]

        try:
            # Step 1 — Read the Excel file
            df = read_excel_file(filename, sheet)

            # Step 2 — Validate columns
            validate_columns(df, expected, filename)

            # Step 3 — Print summary
            print_summary(df, filename)

            # Step 4 — Save to CSV
            save_csv(df, output)

            success_count += 1

        except SystemExit:
            raise

        except Exception as e:
            logger.error(f"Unexpected error processing {filename}: {e}")
            raise

    logger.info("=" * 60)
    logger.info(f"ETL Script 01 — COMPLETED — {success_count}/7 files extracted")
    logger.info(f"Raw CSVs saved to: {RAW_DIR}")
    logger.info("=" * 60)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    extract_all()