"""Đo TỪNG đường API một ở mức 1/10/50 người gọi cùng lúc (chạy trong container api).

Bản `measure-concurrency.py` bắn mọi đường cùng lúc nên một đường chậm kéo cả bảng —
bản này tách riêng để biết đường nào chậm, và in p50/p95/max + số lỗi."""
import concurrent.futures as cf
import statistics
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
EID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
ENDPOINTS = [
    "/api/leave-balances/close-year/review",
    f"/api/employees/{EID}/pending-work",
    "/api/org-chart",
    "/api/work/lists/1/trash",
    "/api/reports/procurement/summary",
]


def login() -> str:
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin"}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["access_token"]


def run(client, path, headers, n):
    def one(_):
        t = time.perf_counter()
        try:
            r = client.get(path, headers=headers, timeout=60)
            return (time.perf_counter() - t) * 1000, r.status_code
        except Exception as exc:  # why: đếm lỗi mạng như một lần hỏng, không dừng cả đợt đo
            return (time.perf_counter() - t) * 1000, type(exc).__name__
    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        res = list(ex.map(one, range(n * 3)))
    ms = sorted(r[0] for r in res)
    bad = [r[1] for r in res if r[1] != 200]
    p95 = ms[int(len(ms) * 0.95) - 1]
    return statistics.median(ms), p95, ms[-1], len(res), bad


def main():
    headers = {"Authorization": f"Bearer {login()}"}
    with httpx.Client(base_url=BASE, limits=httpx.Limits(max_connections=100)) as client:
        for path in ENDPOINTS:
            client.get(path, headers=headers, timeout=60)  # làm nóng
            for n in (1, 10, 50):
                p50, p95, mx, total, bad = run(client, path, headers, n)
                print(f"{path:45s} x{n:<3d} p50={p50:7.0f} p95={p95:7.0f} max={mx:7.0f} ms  "
                      f"lỗi={len(bad)}/{total} {sorted(set(map(str, bad)))[:3]}", flush=True)


if __name__ == "__main__":
    main()
