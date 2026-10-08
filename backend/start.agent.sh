#!/bin/sh
# Khởi động DỊCH VỤ AI (ai-CR-119, AGENT_MODE=service): chờ DB `agent_hub` → alembic riêng → uvicorn app.agent_main.
set -e

echo "Waiting for agent database..."
python - <<'PY'
import os, time, pymysql
for i in range(60):
    try:
        pymysql.connect(host=os.getenv("DB_HOST", "db"), port=int(os.getenv("DB_PORT", "3306")),
                        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
                        database=os.getenv("DB_NAME")).close()
        print("Agent database is ready.")
        break
    except Exception as e:
        print(f"  db not ready ({i}): {e}")
        time.sleep(2)
else:
    raise SystemExit("Agent database not reachable")
PY

echo "Preparing agent schema..."
alembic -c alembic_agent.ini upgrade head

echo "Starting agent-api..."
exec uvicorn app.agent_main:app --host 0.0.0.0 --port 8000 --workers ${AGENT_API_WORKERS:-1}
