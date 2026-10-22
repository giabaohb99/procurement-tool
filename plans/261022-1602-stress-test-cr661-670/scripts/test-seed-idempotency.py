"""Test idempotency of help seed scripts.

Run each help seed script 3 times and verify:
  1. Help article counts per root don't grow after first run
  2. No exceptions
  3. No duplicate articles (same parent_id+title)

Also run 2 copies of seed_help_thu_mua_cap_nhat.py concurrently and check for duplicates.

Run from inside the api container:
  python3 scripts/test-seed-idempotency.py
Writes results to plans/261022-1602-stress-test-cr661-670/results/seed-idempotency.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.modules.help_center.model import HelpArticle, HelpArticleRoot

DB_URL = "mysql+pymysql://root:root_password@db:3306/procurement?charset=utf8mb4"
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

HELP_SEED_SCRIPTS = [
    "python -m app.seed_help_nghi_phep",
    "python -m app.seed_help_van_ban",
    "python -m app.seed_help_cong_viec",
    "python -m app.seed_help_nhan_su",
]

def count_articles_by_root() -> dict:
    """Count help articles per root."""
    db = Session()
    try:
        # Count articles per root_code
        result = db.execute(
            select(HelpArticleRoot.code, func.count(HelpArticle.id))
            .join(HelpArticleRoot)
            .group_by(HelpArticleRoot.code)
        ).all()
        return {code: count for code, count in result}
    finally:
        db.close()

def check_duplicates() -> list[dict]:
    """Check for duplicate articles (same parent_id + title)."""
    db = Session()
    try:
        duplicates = []
        # Find duplicates by parent_id + title
        result = db.execute(
            select(
                HelpArticle.parent_id,
                HelpArticle.title,
                func.count(HelpArticle.id).label("cnt")
            )
            .group_by(HelpArticle.parent_id, HelpArticle.title)
            .filter(func.count(HelpArticle.id) > 1)
        ).all()

        for parent_id, title, cnt in result:
            duplicates.append({
                "parent_id": parent_id,
                "title": title,
                "count": cnt,
            })
        return duplicates
    finally:
        db.close()

def run_script(script_cmd: str) -> dict:
    """Run a seed script and capture result."""
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            script_cmd,
            shell=True,
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=60,
        )
        elapsed = time.perf_counter() - t0
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "elapsed_s": round(elapsed, 1),
            "stderr": result.stderr[:500] if result.stderr else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": "TIMEOUT",
            "elapsed_s": round(time.perf_counter() - t0, 1),
            "stderr": "Script timeout (60s)",
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": f"ERR:{exc.__class__.__name__}",
            "elapsed_s": round(time.perf_counter() - t0, 1),
            "stderr": str(exc),
        }

def test_script_idempotency(script_cmd: str, script_name: str) -> dict:
    """Run script 3 times and check article counts don't grow."""
    counts_by_run = []

    for run_num in range(3):
        print(f"  Run {run_num + 1}/3 of {script_name}...", flush=True)
        result = run_script(script_cmd)
        counts = count_articles_by_root()

        counts_by_run.append({
            "run": run_num + 1,
            "script_result": result,
            "article_counts": counts,
        })

        if not result["ok"]:
            print(f"    ERROR: {result['stderr']}", flush=True)

    # Check idempotency: counts should be same in runs 2 and 3
    run1_counts = counts_by_run[0]["article_counts"]
    run2_counts = counts_by_run[1]["article_counts"]
    run3_counts = counts_by_run[2]["article_counts"]

    idempotent = (run1_counts == run2_counts) and (run2_counts == run3_counts)

    return {
        "script": script_name,
        "idempotent": idempotent,
        "count_growth": {
            "run1_to_run2": {
                k: (run2_counts.get(k, 0) - run1_counts.get(k, 0))
                for k in set(list(run1_counts.keys()) + list(run2_counts.keys()))
            },
            "run2_to_run3": {
                k: (run3_counts.get(k, 0) - run2_counts.get(k, 0))
                for k in set(list(run2_counts.keys()) + list(run3_counts.keys()))
            },
        },
        "run_results": [{"run": r["run"], "ok": r["script_result"]["ok"]} for r in counts_by_run],
    }

def test_concurrent_seed():
    """Run 2 copies of seed_help_thu_mua_cap_nhat.py concurrently."""
    import concurrent.futures as cf

    script_cmd = "python -m app.seed_help_thu_mua_cap_nhat"

    print("Running 2 concurrent copies of seed_help_thu_mua_cap_nhat...", flush=True)

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_script, script_cmd) for _ in range(2)]
        results = [f.result() for f in cf.as_completed(futs)]
    elapsed = time.perf_counter() - t0

    # Check for duplicates after concurrent run
    duplicates = check_duplicates()

    return {
        "concurrent_runs": results,
        "elapsed_s": round(elapsed, 1),
        "duplicates_found": len(duplicates),
        "duplicates": duplicates,
    }

def main() -> None:
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "idempotency_tests": [],
        "concurrent_test": None,
        "final_duplicates": [],
    }

    print("=== Testing seed script idempotency ===\n", flush=True)

    for script_cmd in HELP_SEED_SCRIPTS:
        script_name = script_cmd.split(".")[-1]
        print(f"Testing {script_name}...", flush=True)
        res = test_script_idempotency(script_cmd, script_name)
        results["idempotency_tests"].append(res)
        print(f"  Idempotent: {res['idempotent']}\n", flush=True)

    print("=== Testing concurrent seed execution ===\n", flush=True)
    results["concurrent_test"] = test_concurrent_seed()
    print(f"Duplicates found: {results['concurrent_test']['duplicates_found']}\n", flush=True)

    # Final check for any duplicates
    print("=== Final duplicate check ===\n", flush=True)
    duplicates = check_duplicates()
    results["final_duplicates"] = duplicates

    if duplicates:
        print(f"WARNING: Found {len(duplicates)} duplicate articles", flush=True)
        for dup in duplicates:
            print(f"  parent_id={dup['parent_id']}, title={dup['title']}, count={dup['count']}", flush=True)
    else:
        print("No duplicates found", flush=True)

    # Write results
    import pathlib
    out_file = pathlib.Path("/tmp/results-seed-idempotency.json")
    out_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nWrote {out_file}", flush=True)

if __name__ == "__main__":
    main()
