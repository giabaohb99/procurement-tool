#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import os, time, pymysql
for i in range(60):
    try:
        pymysql.connect(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        ).close()
        print("Database is ready.")
        break
    except Exception as e:
        print(f"  db not ready ({i}): {e}")
        time.sleep(2)
else:
    raise SystemExit("Database not reachable")
PY

echo "Preparing schema..."
python - <<'PY'
import app.core.all_models  # noqa: F401  (đăng ký toàn bộ model)
from sqlalchemy import inspect, create_engine
from alembic.config import Config
from alembic import command
from app.core.config import settings
from app.core.base_model import Base
eng = create_engine(settings.db_url)
cfg = Config("alembic.ini")
if "alembic_version" not in inspect(eng).get_table_names():
    print("  DB trống -> tạo schema từ models (create_all) + stamp head")
    Base.metadata.create_all(eng)
    command.stamp(cfg, "head")
else:
    print("  DB đã có -> alembic upgrade head")
    command.upgrade(cfg, "head")
PY

echo "Seeding data..."
python -m app.seed

echo "Starting API (production, no reload)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
