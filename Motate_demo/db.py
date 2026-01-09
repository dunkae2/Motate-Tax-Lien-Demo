from pathlib import Path
import os
import psycopg

def get_conn():
    db_url = os.getenv("DATABASE_URL", "postgresql://motate:motate@localhost:5432/taxliens")
    return psycopg.connect(db_url)

def init_db():
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO jurisdiction (name, code) VALUES (%s, %s) "
                "ON CONFLICT (code) DO NOTHING",
                ("District of Columbia", "DC"),
            )
        conn.commit()



if __name__ == "__main__":
    init_db()
    print("DB initialized")