# Nifty 100 Financial Intelligence Platform

**Bluestock Fintech — Data Analytics Internship Project**
Individually built end-to-end financial intelligence system covering ETL, a star-schema data warehouse, Power BI analytics, Python/ML analysis, and a Django web application with a partner-facing REST API.

> This project was completed as part of the Bluestock Fintech internship program. The functional specification (data model, dashboard requirements, API design, and week-by-week plan) was provided by Bluestock; all code, pipelines, dashboards, notebooks, and the application itself were independently designed, built, and tested by me as a solo contributor.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Pipeline (ETL)](#data-pipeline-etl)
- [Data Warehouse — Star Schema](#data-warehouse--star-schema)
- [Power BI Dashboards](#power-bi-dashboards)
- [Python Analytics & ML Notebooks](#python-analytics--ml-notebooks)
- [Django Web Application](#django-web-application)
- [Channel Partner API](#channel-partner-api)
- [Security](#security)
- [Setup & Installation](#setup--installation)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Author](#author)

---

## Overview

The Nifty 100 Financial Intelligence Platform ingests ~12 years of historical financial data for India's top 100 listed companies and turns it into:

1. **A clean, query-ready PostgreSQL data warehouse** (star schema)
2. **7 production-style Power BI dashboards** for executives, analysts, and risk/credit teams
3. **A Python analytics layer** producing rule-based health scores, anomaly flags, sector clusters, peer similarity mappings, and revenue forecasts
4. **A public Django website** for browsing, screening, and comparing companies
5. **A secured, rate-limited REST API** for channel partners, authenticated via HMAC-SHA256 signed requests

| Stream | Focus | Approx. Effort Split |
|---|---|---|
| Data Engineering | MySQL dump → ETL → PostgreSQL star schema | 35% |
| Power BI Analytics | 7 dashboards, 25+ DAX measures | 40% |
| Django Web App & API | Public site + channel partner API | 25% |

## Architecture

```
MySQL/MariaDB SQL Dump (source)
        │
        ▼
  Python ETL (pandas, regex parsing, cleaning, derived metrics)
        │
        ▼
  PostgreSQL — Star Schema Data Warehouse
        │
        ├──────────────► Power BI Desktop / Power BI Service (7 dashboards)
        │
        ├──────────────► Python ML Engine (Jupyter notebooks)
        │                 health scores · anomaly flags · clusters · forecasts
        │                       │
        │                       ▼
        │                 written back to PostgreSQL
        │
        └──────────────► Django + DRF
                          ├── Public website (search, screener, compare, charts)
                          ├── Public REST API
                          └── Channel Partner API (HMAC-SHA256 auth, tiered rate limits)
```

## Tech Stack

**Data Engineering:** Python 3.11, pandas, SQLAlchemy, psycopg2, PostgreSQL 15
**Analytics / ML:** scikit-learn, scipy, statsmodels, matplotlib, seaborn, Jupyter
**BI:** Microsoft Power BI Desktop, DAX, Power Query (M)
**Backend:** Django 4.2, Django REST Framework, drf-spectacular, Celery, Redis
**Auth & Security:** HMAC-SHA256, bcrypt, JWT (`djangorestframework-simplejwt`), python-decouple
**Frontend:** Django templates, Tailwind CSS, Chart.js
**Quality:** pytest, pytest-cov, bandit, safety, black, isort, flake8
**Infra:** Docker, Docker Compose, Git

## Project Structure

```
nifty100-platform/
├── etl/
│   ├── 01_extract_from_mysql.py
│   ├── 02_clean_and_transform.py
│   ├── 03_load_to_warehouse.py
│   └── schema.sql
├── data/
│   ├── raw/
│   ├── clean/
│   └── sector_mapping.csv
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_health_scoring.ipynb
│   ├── 03_anomaly_detection.ipynb
│   ├── 04_sector_clustering.ipynb
│   ├── 05_peer_comparison.ipynb
│   └── 06_trend_forecasting.ipynb
├── powerbi/
│   ├── 01_executive_overview.pbix
│   ├── 02_company_deep_dive.pbix
│   ├── 03_sector_comparison.pbix
│   ├── 04_health_scorecard.pbix
│   ├── 05_growth_analytics.pbix
│   ├── 06_debt_leverage.pbix
│   └── 07_dividend_returns.pbix
├── bluestock/                  # Django project
│   ├── companies/
│   ├── ml_engine/
│   ├── api_management/
│   ├── dashboard/
│   └── accounts/
├── tests/
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Data Pipeline (ETL)

Source data: a MariaDB/MySQL SQL dump containing 7 tables — `companies`, `analysis`, `balancesheet`, `profitandloss`, `cashflow`, `prosandcons`, `documents` — covering ~12 years per company across 100 Nifty 100 constituents.

**`01_extract_from_mysql.py`** — Regex-parses `INSERT INTO` statements directly from the SQL dump (no live MySQL instance required), handling escaped quotes and `NULL` tokens, and writes one clean CSV per table to `data/raw/`.

**`02_clean_and_transform.py`** — Standardizes inconsistent year formats (`Mar-24`, `Mar 2024`, `TTM`) into a single `MMM YYYY` convention with derived `fiscal_year` and `sort_order` fields; parses free-text growth strings (e.g. `"10 Years: 11%"`) into structured `period` / `value_pct` columns; manually maps all 100 companies to sectors; computes derived financial metrics (debt-to-equity, net profit margin, free cash flow, interest coverage, and others).

**`03_load_to_warehouse.py`** — Loads dimension tables first, then fact tables with FK references, using `ON CONFLICT DO UPDATE` upserts so the pipeline is safely re-runnable. Runs post-load row-count verification and data quality checks.

## Data Warehouse — Star Schema

**Dimensions:** `dim_company`, `dim_year`, `dim_sector`, `dim_health_label`
**Facts:** `fact_profit_loss`, `fact_balance_sheet`, `fact_cash_flow`, `fact_analysis`, `fact_ml_scores`, `fact_pros_cons`

Key design decisions:
- `symbol` (string, e.g. `TCS`) is the join key across all fact tables — not a surrogate integer ID, matching the source system's natural key.
- `dim_year.is_ttm` and `sort_order` separate Trailing-Twelve-Month rows from historical years and drive correct chronological ordering, since TTM periods are excluded from CAGR/growth calculations to avoid distortion.
- All monetary figures are stored and displayed in **INR Crores**.

## Power BI Dashboards

Seven dashboards, all connected live to PostgreSQL, sharing a unified visual design system (color-coded for good/warning/bad, consistent typography, consistent footer disclaimer):

| # | Dashboard | Audience | Pages |
|---|---|---|---|
| 1 | Executive Market Overview | Fund managers, CXOs | 3 |
| 2 | Company Deep Dive | Individual investors, analysts | 4 |
| 3 | Sector Comparison Analyzer | Cross-sector analysts | 3 |
| 4 | Financial Health Scorecard | Risk analysts, portfolio managers | 2 |
| 5 | Growth & Valuation Analytics | Growth investors | 3 |
| 6 | Debt & Leverage Monitor | Credit analysts, risk managers | 2 |
| 7 | Dividend & Shareholder Returns | Income investors | 2 |

Built on a library of 25+ DAX measures covering revenue, profitability, leverage, cash flow, dividends, and ML health scores, with relationships modeled many-to-one from each fact table into `dim_company` and `dim_year`.

## Python Analytics & ML Notebooks

| Notebook | Technique | Output |
|---|---|---|
| EDA | Null-value heatmaps, distribution analysis, `seaborn` boxplots, correlation matrix, IQR/Z-score outlier detection | Insight summary, 20+ visualizations |
| Health Scoring | Weighted 6-dimension composite score (profitability, growth, leverage, cash flow, dividend, trend) | Per-company score + label, loaded to PostgreSQL |
| Anomaly Detection | Z-score method + Isolation Forest, compared | Flagged company-years, loaded to PostgreSQL |
| Sector Clustering | K-Means (K=5), PCA for visualization | Cluster assignments + descriptions |
| Peer Comparison | Cosine similarity over financial feature vectors | `peer_mapping.csv` |
| Trend Forecasting | ARIMA | 1-year revenue forecasts for top 20 companies |

**Methodology note (important for technical readers):** the health scoring engine is a **rule-based / heuristic composite score**, not a trained predictive model — this is an intentional design choice for financial scoring, where interpretability matters more than black-box accuracy. The genuine machine learning components in this project are **Isolation Forest** (anomaly detection) and **K-Means** (clustering); **ARIMA** forecasting is a classical statistical method, not ML. This project deliberately avoids over-labeling rule-based logic as "ML."

Scheduled refresh of scoring and anomaly detection is handled via **Celery + Celery Beat**, writing results back to PostgreSQL on a recurring schedule.

## Django Web Application

| Page | Description |
|---|---|
| `/` | Search, featured companies, sector cards, insights ticker |
| `/companies/` | Filterable, sortable company table |
| `/company/{symbol}/` | Full company detail: health score gauge, 8 Chart.js visualizations, pros/cons, annual report links |
| `/compare/` | Side-by-side comparison of 2–4 companies |
| `/screener/` | Multi-filter financial screener |
| `/sector/{name}/` | Sector roll-up with combined performance chart |

**Company detail page charts (8):** revenue & profit trend, balance sheet composition, cash flow waterfall, EPS & dividend history, debt vs. equity, CAGR radar, margin trend, and a health-score gauge — all rendered with Chart.js, fed by a dedicated `/api/v1/companies/{symbol}/charts/` endpoint, with Redis caching (60-minute TTL) on the most-requested financial data responses.

Apps: `companies`, `ml_engine`, `api_management`, `dashboard`, `accounts` (JWT auth, admin/permissions).

## Channel Partner API

A REST API for external partners to programmatically pull financial data, authenticated via **HMAC-SHA256 request signing** rather than simple API keys:

```
X-API-Key-ID:  <partner key id>
X-Timestamp:   <unix timestamp>
X-Nonce:       <unique per-request nonce>
X-Signature:   <HMAC-SHA256 signature>
```

Signatures are verified server-side using `secrets.compare_digest()` to prevent timing attacks. The timestamp + nonce combination guards against replay attacks.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/partner/v1/companies/{symbol}/full/` | Full financial data for one company |
| GET | `/api/partner/v1/bulk-financials/` | Multi-company pull via `?symbols=` |
| GET | `/api/partner/v1/screener/` | Financial screener with full filter support |
| GET | `/api/partner/v1/scores/` | ML/health scores for all companies |
| POST | `/api/partner/v1/keys/` | Create a new API key (secret shown once) |
| POST | `/api/partner/v1/webhooks/` | Subscribe to `score_updated` / `anomaly_flagged` events |

**Tiered rate limiting** (Redis-backed, enforced per minute/hour/day):

| Tier | Per Minute | Per Hour | Per Day |
|---|---|---|---|
| BASIC | 10 | 100 | 500 |
| PRO | 60 | 1,000 | 10,000 |
| ENTERPRISE | 300 | 10,000 | 100,000 |

## Security

- All secrets managed via `python-decouple` and `.env` (excluded from version control)
- API partner secrets are stored securely server-side and never logged or returned after initial creation
- All signature comparisons use `secrets.compare_digest()` to prevent timing-based attacks
- DRF serializers validate all API input; bulk CSV imports validate MIME type, file size, and column structure before processing
- Rate limits enforced at multiple tiers: anonymous public API, authenticated admin API, and per-partner-tier channel API
- Static analysis via `bandit` and dependency vulnerability scanning via `safety` run across the codebase, with all high-severity findings resolved

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/muhammedfahim438-ctrl/nifty100-platform.git
cd nifty100-platform

# Environment
cp .env.example .env   # fill in SECRET_KEY, DATABASE_URL, REDIS_URL, etc.
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Data pipeline
python etl/01_extract_from_mysql.py
python etl/02_clean_and_transform.py
python etl/03_load_to_warehouse.py

# Django
python manage.py migrate
python manage.py runserver

# Background tasks
celery -A bluestock worker -l info
celery -A bluestock beat -l info

# Or run the full stack
docker-compose up --build
```

Power BI: open any `.pbix` file in `powerbi/`, point the PostgreSQL connection at your local warehouse (`localhost:5432`, database `bluestock_dw`), and refresh.

## Testing

```bash
pytest --cov=. --cov-report=html
black . && isort . && flake8 .
bandit -r . -ll
safety check
```

Test coverage target: 75%+, including dedicated tests for HMAC authentication (valid, expired, and tampered signature cases).

## Known Limitations

In the interest of giving an accurate technical picture rather than an idealized one:

- The health scoring engine is rule-based, not a trained/validated ML model — see the methodology note above.
- Regex-based SQL dump parsing is a pragmatic one-time ETL approach rather than a production-grade ingestion method, and is sensitive to malformed or unusual source rows.
- ARIMA forecasts are not currently backtested against a holdout period, so no accuracy metric (e.g. MAPE) is reported for the forecasting notebook.
- For banking and NBFC companies (HDFCBANK, AXISBANK, BANKBARODA, BAJFINANCE, BAJAJFINSV), the `borrowings` field includes customer deposits, so D/E ratios for these companies are not directly comparable to non-financial companies — this is called out in the dashboards but is a structural limitation of the source data, not something ETL can fully normalize.

## Author

**Muhammed Fahim**
Built solo as part of the Bluestock Fintech Data Analytics Internship.
GitHub: [github.com/muhammedfahim438-ctrl/nifty100-platform](https://github.com/muhammedfahim438-ctrl/nifty100-platform)

---

*Data is presented for educational purposes only and does not constitute financial advice.*