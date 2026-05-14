from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:postgres123@localhost:5432/nifty100')

with engine.connect() as conn:
    conn.execute(text("INSERT INTO dim_sector (sector_name, sector_code) VALUES ('Finance', 'FIN')"))
    conn.commit()
    result = conn.execute(text("SELECT COUNT(*) FROM dim_sector"))
    print("Rows in dim_sector:", result.scalar())