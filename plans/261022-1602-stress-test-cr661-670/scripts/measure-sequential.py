"""Load test for new endpoints from CR-661..670 (f1f25b23, d5e339c9, eda06696, f194c0a8, 1892d6be).

Measures sequential (1x concurrency) latency, SQL statement count, and error rate.

New endpoints:
  - CR-661/664: GET /api/leave-balances/close-year/review (with optional /export)
  - CR-665: GET /api/employees/{eid}/pending-work
  - CR-666/667: GET /api/tasks/lists/{list_id}/trash, GET /api/tasks/{task_id}/comments
  - CR-669: GET /api/org-chart
  - CR-662/663: GET /api/reports/procurement/summary (department grouping)

Run from inside the api container:
  python3 scripts/measure-sequential.py [--quick]
Writes plans/261022-1602-stress-test-cr661-670/results/sequential.json.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

os.environ["REPORT_CACHE_TTL"] = "0"  # Measure without cache

import pymysql
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

pymysql.connect(host="db", port=3306, user="root", password="root_password",
                database="procurement").close()

DB_URL = "mysql+pymysql://root:root_password@db:3306/procurement?charset=utf8mb4"
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

import sys
sys.path.insert(0, "/app")

import app.main as app_main
from app.core.database import get_db
from fastapi.testclient import TestClient

def _get_test_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

app_main.app.dependency_overrides[get_db] = _get_test_db
client = TestClient(app_main.app)

_sql_stats = {"count": 0}

@event.listens_for(engine, "before_cursor_execute")
def _before(conn, cursor, statement, parameters, context, executemany):
    context._t0 = time.perf_counter()

@event.listens_for(engine, "after_cursor_execute")
def _after(conn, cursor, statement, parameters, context, executemany):
    _sql_stats["count"] += 1

def reset_sql_stats():
    _sql_stats["count"] = 0

def login(username: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["data"]["access_token"]

TOKEN = login("admin", "admin")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# New endpoints from the 5 commits
ENDPOINTS = [
    # CR-661/664: Leave carryover review
    ("leave_close_year_review", "/api/leave-balances/close-year/review", {}),

    # CR-665: Employee pending work
    ("employee_pending_work", "/api/employees/17/pending-work", {}),  # admin user id

    # CR-669: Organization chart
    ("org_chart", "/api/org-chart", {}),

    # CR-666: Work trash list (for a list)
    ("work_trash", "/api/work/lists/1/trash", {}),  # assume list_id=1 exists

    # CR-662/663: Procurement report summary grouped by department
    ("procurement_summary_dept", "/api/reports/procurement/summary", {"group_by": "department"}),
    ("procurement_summary_none", "/api/reports/procurement/summary", {}),
]

def call_once(path: str, params: dict) -> dict:
    reset_sql_stats()
    t0 = time.perf_counter()
    r = client.get(path, params=params, headers=HEADERS)
    wall_ms = (time.perf_counter() - t0) * 1000
    ok = r.status_code == 200
    return {
        "status": r.status_code,
        "ok": ok,
        "wall_ms": wall_ms,
        "sql_count": _sql_stats["count"],
        "body_bytes": len(r.content) if ok else 0,
    }

def measure_endpoint(path: str, params: dict, reps: int = 20) -> dict:
    """Run endpoint multiple times, skip first rep as warmup, report stats on rest."""
    results = [call_once(path, params) for _ in range(reps)]
    kept = results[1:]  # Skip warmup
    ok_kept = [x for x in kept if x["ok"]]

    out = {
        "params": params,
        "reps_ok": len(ok_kept),
        "reps_total": len(kept),
        "errors": [x["status"] for x in kept if not x["ok"]],
    }

    if ok_kept:
        wall = [x["wall_ms"] for x in ok_kept]
        out.update({
            "p50_ms": round(statistics.median(wall), 1),
            "p95_ms": round(sorted(wall)[min(len(wall) - 1, int(len(wall) * 0.95))], 1),
            "max_ms": round(max(wall), 1),
            "sql_count": ok_kept[-1]["sql_count"],
            "body_bytes": ok_kept[-1]["body_bytes"],
        })

    return out

def main() -> None:
    import datetime
    quick = "--quick" in sys.argv

    results: dict = {}
    t_start = time.perf_counter()

    for key, path, params in ENDPOINTS:
        print(f"[{key}] {path} ...", flush=True)
        t0 = time.perf_counter()
        reps = 5 if quick else 20
        res = measure_endpoint(path, params, reps=reps)
        dt = time.perf_counter() - t0
        print(f"  -> p50={res.get('p50_ms')} ms, p95={res.get('p95_ms')} ms, "
              f"max={res.get('max_ms')} ms, sql={res.get('sql_count')}, "
              f"ok={res.get('reps_ok')}/{res.get('reps_total')}, "
              f"errors={res.get('errors')} (took {dt:.1f}s)", flush=True)
        results[key] = res

    total_s = time.perf_counter() - t_start
    output = {"results": results, "total_seconds": round(total_s, 1)}

    # Write results
    import pathlib
    pathlib.Path("/tmp/results-sequential.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nTotal sequential time: {total_s:.1f}s")
    print("Wrote /tmp/results-sequential.json")

if __name__ == "__main__":
    main()
