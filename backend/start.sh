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

echo "Running DB migrations (alembic)..."
alembic upgrade head

echo "Seeding data..."
python -m app.seed

echo "Starting API (reload)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
