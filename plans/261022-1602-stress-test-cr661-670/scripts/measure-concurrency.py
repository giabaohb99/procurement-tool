"""Concurrent load test for CR-661..670 endpoints at 1x, 10x, 50x concurrency.

Run from inside the api container:
  python3 scripts/measure-concurrency.py
Writes plans/261022-1602-stress-test-cr661-670/results/concurrent-1x.json,
        plans/261022-1602-stress-test-cr661-670/results/concurrent-10x.json,
        plans/261022-1602-stress-test-cr661-670/results/concurrent-50x.json.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"

# New endpoints from CR-661..670
ENDPOINTS = [
    "/api/leave-balances/close-year/review",
    "/api/employees/17/pending-work",
    "/api/org-chart",
    "/api/work/lists/1/trash",
    "/api/reports/procurement/summary",
]

def login() -> str:
    r = httpx.post(f"{BASE}/api/auth/login",
                    json={"username": "admin", "password": "admin"},
                    timeout=10)
    r.raise_for_status()
    return r.json()["data"]["access_token"]

def fire(path: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    t0 = time.perf_counter()
    try:
        r = httpx.get(path, headers=headers, timeout=60)
        return {
            "path": path,
            "ms": (time.perf_counter() - t0) * 1000,
            "status": r.status_code,
            "ok": r.status_code == 200,
        }
    except httpx.TimeoutException:
        return {
            "path": path,
            "ms": (time.perf_counter() - t0) * 1000,
            "status": "TIMEOUT",
            "ok": False,
        }
    except Exception as exc:
        return {
            "path": path,
            "ms": (time.perf_counter() - t0) * 1000,
            "status": f"ERR:{exc.__class__.__name__}",
            "ok": False,
        }

def summarize(label: str, calls: list[dict]) -> dict:
    oks = [c for c in calls if c["ok"]]
    errs = [c for c in calls if not c["ok"]]
    ms = sorted(c["ms"] for c in oks)

    def pct(p):
        if not ms:
            return None
        idx = min(len(ms) - 1, int(len(ms) * p))
        return round(ms[idx], 1)

    return {
        "label": label,
        "total_calls": len(calls),
        "ok": len(oks),
        "errors": len(errs),
        "error_statuses": sorted({str(c["status"]) for c in errs}),
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "max_ms": round(ms[-1], 1) if ms else None,
    }

def run_concurrent(n_users: int, token: str) -> dict:
    """Run all endpoints with n_users concurrent clients."""
    tasks = [(path, token) for _ in range(n_users) for path in ENDPOINTS]

    t0 = time.perf_counter()
    with httpx.Client(base_url=BASE) as client:
        with cf.ThreadPoolExecutor(max_workers=min(len(tasks), 300)) as ex:
            # Create fire function that uses the shared client
            def fire_with_client(path, token):
                headers = {"Authorization": f"Bearer {token}"}
                t_start = time.perf_counter()
                try:
                    r = client.get(path, headers=headers, timeout=60)
                    return {
                        "path": path,
                        "ms": (time.perf_counter() - t_start) * 1000,
                        "status": r.status_code,
                        "ok": r.status_code == 200,
                    }
                except httpx.TimeoutException:
                    return {
                        "path": path,
                        "ms": (time.perf_counter() - t_start) * 1000,
                        "status": "TIMEOUT",
                        "ok": False,
                    }
                except Exception as exc:
                    return {
                        "path": path,
                        "ms": (time.perf_counter() - t_start) * 1000,
                        "status": f"ERR:{exc.__class__.__name__}",
                        "ok": False,
                    }

            futs = [ex.submit(fire_with_client, path, tok) for path, tok in tasks]
            calls = [f.result() for f in futs]

    wall_s = time.perf_counter() - t0
    label = f"concurrency n_users={n_users}"
    out = summarize(label, calls)
    out["wall_seconds_total_batch"] = round(wall_s, 1)
    return out

def main() -> None:
    print("Logging in...", flush=True)
    token = login()
    print(f"Token acquired: {token[:20]}...", flush=True)

    results = {}

    for n_users in [1, 10, 50]:
        print(f"\n=== Running with {n_users} concurrent users ===", flush=True)
        result = run_concurrent(n_users, token)
        results[f"{n_users}x"] = result
        print(f"  p50={result['p50_ms']}ms, p95={result['p95_ms']}ms, "
              f"max={result['max_ms']}ms, ok={result['ok']}, "
              f"errors={result['errors']}", flush=True)

        # Write partial results
        import pathlib
        pathlib.Path("/tmp/results-concurrent.json").write_text(
            json.dumps(results, indent=2, default=str))

    print("\nWrote /tmp/results-concurrent.json", flush=True)

if __name__ == "__main__":
    main()
