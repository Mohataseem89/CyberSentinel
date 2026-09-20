"""Idempotent production schema bootstrap/migration runner."""
from pathlib import Path
from sqlalchemy import text
from models import Base, engine

MIGRATIONS=Path(__file__).resolve().parents[1]/"migrations"

def main():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"))
        applied={r[0] for r in conn.execute(text("SELECT name FROM schema_migrations"))}
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if path.name in applied: continue
            sql=path.read_text(encoding="utf-8")
            conn.exec_driver_sql(sql)
            conn.execute(text("INSERT INTO schema_migrations(name) VALUES (:name)"),{"name":path.name})
            print(f"Applied {path.name}")
    print("Database schema is current.")

if __name__=="__main__": main()
