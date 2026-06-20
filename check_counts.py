import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5433")
DB_NAME     = os.getenv("DB_NAME",     "nifty100")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = sqlalchemy.create_engine(DATABASE_URL)

tables = [
    'dim_sector', 
    'dim_company', 
    'dim_year', 
    'dim_health_label', 
    'fact_profit_loss', 
    'fact_balance_sheet', 
    'fact_cash_flow', 
    'fact_analysis', 
    'fact_pros_cons', 
    'fact_documents', 
    'fact_ml_scores'
]

with engine.connect() as conn:
    for tbl in tables:
        try:
            res = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            print(f"{tbl}: {res}")
        except Exception as e:
            print(f"{tbl}: ERROR: {e}")
