from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine('postgresql+psycopg2://postgres:postgres123@localhost:5433/nifty100')

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT symbol, health_label FROM fact_ml_scores WHERE health_label = 'UNKNOWN' ORDER BY symbol"
    ))
    print("Companies with UNKNOWN scores:")
    for r in result:
        print(f"  {r[0]}")