"""
Fix NaN health scores — recomputes scores for companies
that have NaN or missing values in fact_ml_scores.
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER','postgres')}:"
    f"{os.getenv('DB_PASSWORD','postgres123')}@"
    f"{os.getenv('DB_HOST','localhost')}:"
    f"{os.getenv('DB_PORT','5433')}/"
    f"{os.getenv('DB_NAME','nifty100')}"
)
engine = create_engine(DATABASE_URL)

# ── Load data ──
print("Loading data...")

df_pl = pd.read_sql("""
    SELECT fpl.symbol, AVG(fpl.opm_pct) as avg_opm,
           AVG(fpl.net_profit_margin_pct) as avg_margin,
           AVG(CASE WHEN fpl.interest_coverage < 500 
               THEN fpl.interest_coverage END) as avg_coverage,
           AVG(CASE WHEN fpl.eps < 1000 
               THEN fpl.eps END) as avg_eps,
           SUM(CASE WHEN fpl.net_profit > 0 THEN 1 ELSE 0 END) as years_profitable
    FROM fact_profit_loss fpl
    JOIN dim_year dy ON fpl.year_id = dy.year_id
    WHERE dy.is_ttm = FALSE
    GROUP BY fpl.symbol
""", engine)

df_bs = pd.read_sql("""
    SELECT fbs.symbol,
           AVG(CASE WHEN fbs.debt_to_equity < 20 
               THEN fbs.debt_to_equity END) as avg_dte,
           AVG(fbs.equity_ratio) as avg_eq_ratio
    FROM fact_balance_sheet fbs
    JOIN dim_year dy ON fbs.year_id = dy.year_id
    WHERE dy.is_ttm = FALSE
    GROUP BY fbs.symbol
""", engine)

df_cf = pd.read_sql("""
    SELECT fcf.symbol,
           AVG(fcf.free_cash_flow) as avg_fcf,
           AVG(fcf.operating_activity) as avg_op_cf,
           SUM(CASE WHEN fcf.free_cash_flow > 0 THEN 1 ELSE 0 END) as years_pos_fcf
    FROM fact_cash_flow fcf
    JOIN dim_year dy ON fcf.year_id = dy.year_id
    WHERE dy.is_ttm = FALSE
    GROUP BY fcf.symbol
""", engine)

df_div = pd.read_sql("""
    SELECT fpl.symbol,
           AVG(fpl.dividend_payout) as avg_dividend,
           SUM(CASE WHEN fpl.dividend_payout > 0 THEN 1 ELSE 0 END) as years_dividend
    FROM fact_profit_loss fpl
    JOIN dim_year dy ON fpl.year_id = dy.year_id
    WHERE dy.is_ttm = FALSE
    GROUP BY fpl.symbol
""", engine)

# Revenue CAGR
df_rev = pd.read_sql("""
    SELECT symbol,
           FIRST_VALUE(sales) OVER (
               PARTITION BY symbol ORDER BY sort_order
           ) as first_sales,
           LAST_VALUE(sales) OVER (
               PARTITION BY symbol ORDER BY sort_order
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
           ) as last_sales,
           MIN(fiscal_year) OVER (PARTITION BY symbol) as first_year,
           MAX(fiscal_year) OVER (PARTITION BY symbol) as last_year
    FROM fact_profit_loss fpl
    JOIN dim_year dy ON fpl.year_id = dy.year_id
    WHERE dy.is_ttm = FALSE AND sales > 0
""", engine)

df_rev = df_rev.drop_duplicates(subset='symbol')
df_rev['years'] = df_rev['last_year'] - df_rev['first_year']
df_rev['revenue_cagr'] = np.where(
    (df_rev['years'] > 0) & (df_rev['first_sales'] > 0),
    ((df_rev['last_sales'] / df_rev['first_sales']) ** (1 / df_rev['years']) - 1) * 100,
    np.nan
)

df_company = pd.read_sql("SELECT symbol FROM dim_company", engine)

# ── Merge features ──
features = df_company.copy()
features = features.merge(df_pl,  on='symbol', how='left')
features = features.merge(df_bs,  on='symbol', how='left')
features = features.merge(df_cf,  on='symbol', how='left')
features = features.merge(df_div, on='symbol', how='left')
features = features.merge(df_rev[['symbol','revenue_cagr']], on='symbol', how='left')

print(f"Feature matrix: {features.shape}")

# ── Percentile ranking functions ──
def prank(series):
    return series.rank(pct=True, na_option='keep') * 100

def prank_inv(series):
    return (1 - series.rank(pct=True, na_option='keep')) * 100

df = features.copy()

# ── Scores ──
df['p_opm']       = prank(df['avg_opm'].clip(upper=100))
df['p_margin']    = prank(df['avg_margin'].clip(upper=100))
df['p_coverage']  = prank(df['avg_coverage'].clip(upper=500))
df['p_prof_yrs']  = prank(df['years_profitable'])

df['profitability_score'] = (
    df['p_opm']      * 0.35 +
    df['p_margin']   * 0.35 +
    df['p_coverage'] * 0.20 +
    df['p_prof_yrs'] * 0.10
)

df['p_rev_cagr'] = prank(df['revenue_cagr'])
df['p_eps']      = prank(df['avg_eps'].clip(upper=500))

df['growth_score'] = (
    df['p_rev_cagr'] * 0.60 +
    df['p_eps']      * 0.40
)

df['p_dte']      = prank_inv(df['avg_dte'].clip(upper=20))
df['p_eq_ratio'] = prank(df['avg_eq_ratio'])

df['leverage_score'] = (
    df['p_dte']      * 0.60 +
    df['p_eq_ratio'] * 0.40
)

df['p_fcf']     = prank(df['avg_fcf'])
df['p_op_cf']   = prank(df['avg_op_cf'])
df['p_fcf_yrs'] = prank(df['years_pos_fcf'])

df['cashflow_score'] = (
    df['p_fcf']     * 0.40 +
    df['p_op_cf']   * 0.40 +
    df['p_fcf_yrs'] * 0.20
)

df['p_div']     = prank(df['avg_dividend'])
df['p_div_yrs'] = prank(df['years_dividend'])

df['dividend_score'] = (
    df['p_div']     * 0.50 +
    df['p_div_yrs'] * 0.50
)

df['trend_score'] = (
    df['p_rev_cagr']  * 0.50 +
    df['p_prof_yrs']  * 0.50
)

# Fill NaN sub-scores with 50 (median) before computing overall
df['profitability_score'] = df['profitability_score'].fillna(50)
df['growth_score']        = df['growth_score'].fillna(50)
df['leverage_score']      = df['leverage_score'].fillna(50)
df['cashflow_score']      = df['cashflow_score'].fillna(50)
df['dividend_score']      = df['dividend_score'].fillna(50)
df['trend_score']         = df['trend_score'].fillna(50)

df['overall_score'] = (
    df['profitability_score'] * 0.25 +
    df['growth_score']        * 0.20 +
    df['leverage_score']      * 0.20 +
    df['cashflow_score']      * 0.15 +
    df['dividend_score']      * 0.10 +
    df['trend_score']         * 0.10
)

def assign_label(score):
    if pd.isna(score): return 'UNKNOWN'
    elif score >= 85:  return 'EXCELLENT'
    elif score >= 70:  return 'GOOD'
    elif score >= 50:  return 'AVERAGE'
    elif score >= 35:  return 'WEAK'
    else:              return 'POOR'

df['health_label'] = df['overall_score'].apply(assign_label)

score_cols = ['overall_score','profitability_score','growth_score',
              'leverage_score','cashflow_score','dividend_score','trend_score']
df[score_cols] = df[score_cols].round(2)

unknown = df[df['overall_score'].isna()]['symbol'].tolist()
print(f"UNKNOWN companies: {unknown}")
for sym in unknown:
    row = df[df['symbol'] == sym].iloc[0]
    print(f"\n{sym}:")
    print(f"  avg_opm={row.get('avg_opm')}, avg_margin={row.get('avg_margin')}")
    print(f"  avg_dte={row.get('avg_dte')}, avg_eq_ratio={row.get('avg_eq_ratio')}")
    print(f"  avg_fcf={row.get('avg_fcf')}, revenue_cagr={row.get('revenue_cagr')}")
print(f"Label distribution:\n{df['health_label'].value_counts()}")

# ── Delete old scores and insert fresh ──
print("\nUpdating scores in PostgreSQL...")

with engine.connect() as conn:
    conn.execute(text("DELETE FROM fact_ml_scores"))
    conn.commit()

count = 0
with engine.connect() as conn:
    for _, row in df.iterrows():
        def safe(val):
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return None
            return float(val)

        conn.execute(text("""
            INSERT INTO fact_ml_scores (
                symbol, computed_at, overall_score,
                profitability_score, growth_score, leverage_score,
                cashflow_score, dividend_score, trend_score, health_label
            ) VALUES (
                :symbol, :computed_at, :overall_score,
                :profitability_score, :growth_score, :leverage_score,
                :cashflow_score, :dividend_score, :trend_score, :health_label
            )
        """), {
            'symbol'              : row['symbol'],
            'computed_at'         : datetime.now(),
            'overall_score'       : safe(row['overall_score']),
            'profitability_score' : safe(row['profitability_score']),
            'growth_score'        : safe(row['growth_score']),
            'leverage_score'      : safe(row['leverage_score']),
            'cashflow_score'      : safe(row['cashflow_score']),
            'dividend_score'      : safe(row['dividend_score']),
            'trend_score'         : safe(row['trend_score']),
            'health_label'        : row['health_label'],
        })
        count += 1
    conn.commit()

print(f"Updated {count} company scores")

# ── Verify ──
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT health_label, COUNT(*) as count
        FROM fact_ml_scores
        GROUP BY health_label
        ORDER BY count DESC
    """))
    print("\nFinal distribution:")
    for r in result:
        print(f"  {r[0]}: {r[1]}")