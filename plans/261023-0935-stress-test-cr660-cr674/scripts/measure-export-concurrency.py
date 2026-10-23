"""Đo tải HTTP các đường XUẤT của duoc-CR-660 / CR-675 ở 1 / 10 / 50 / 150 người bấm cùng lúc.

Chạy TRONG container api (có httpx, gọi thẳng uvicorn, không qua nginx):
    docker compose cp plans/261023-0935-stress-test-cr660-cr674/scripts/measure-export-concurrency.py api:/tmp/m.py
    docker compose exec -T api python /tmp/m.py > plans/261023-0935-stress-test-cr660-cr674/results/concurrent.json

Cố ý KHÔNG đo `/api/exports/run`: mỗi lượt ghi một tệp + một dòng nhật ký xuất, 150 lượt là rác kho tệp local.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
ENDPOINTS = [
    "/api/employees/export/csv",
    "/api/employees/export/xlsx",
    "/api/products/export/csv",          # 6 803 dòng ở local — đường nặng nhất
    "/api/departments/export/csv",
    "/api/vehicle-bookings/export/xlsx",
    "/api/vehicles/export/xlsx",
]
LEVELS = [1, 10, 50, 150]


def login() -> str:
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin"}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["access_token"]


def fire(client: httpx.Client, path: str, token: str) -> dict:
    t0 = time.perf_counter()
    try:
        r = client.get(path, headers={"Authorization": f"Bearer {token}"}, timeout=90)
        return {"path": path, "ms": (time.perf_counter() - t0) * 1000, "status": r.status_code,
                "ok": r.status_code == 200, "bytes": len(r.content)}
    except httpx.TimeoutException:
        return {"path": path, "ms": (time.perf_counter() - t0) * 1000, "status": "TIMEOUT", "ok": False, "bytes": 0}
    except Exception as exc:  # noqa: BLE001 — đo tải: mọi lỗi đều là một dòng kết quả
        return {"path": path, "ms": (time.perf_counter() - t0) * 1000, "status": f"ERR:{exc.__class__.__name__}",
                "ok": False, "bytes": 0}


def pct(values: list[float], p: float):
    if not values:
        return None
    return round(sorted(values)[min(len(values) - 1, int(len(values) * p))], 1)


def summarize(calls: list[dict]) -> dict:
    oks = [c for c in calls if c["ok"]]
    ms = [c["ms"] for c in oks]
    per_path = {}
    for path in ENDPOINTS:
        mine = [c["ms"] for c in oks if c["path"] == path]
        per_path[path] = {"ok": len(mine), "p50_ms": pct(mine, 0.5), "p95_ms": pct(mine, 0.95),
                          "max_ms": round(max(mine), 1) if mine else None}
    return {"total_calls": len(calls), "ok": len(oks), "errors": len(calls) - len(oks),
            "error_statuses": sorted({str(c["status"]) for c in calls if not c["ok"]}),
            "p50_ms": pct(ms, 0.5), "p95_ms": pct(ms, 0.95), "max_ms": round(max(ms), 1) if ms else None,
            "per_path": per_path}


def run(n_users: int, token: str) -> dict:
    tasks = [path for _ in range(n_users) for path in ENDPOINTS]
    limits = httpx.Limits(max_connections=len(tasks), max_keepalive_connections=len(tasks))
    t0 = time.perf_counter()
    with httpx.Client(base_url=BASE, limits=limits) as client:
        with cf.ThreadPoolExecutor(max_workers=min(len(tasks), 300)) as ex:
            calls = list(ex.map(lambda p: fire(client, p, token), tasks))
    out = summarize(calls)
    out["wall_seconds"] = round(time.perf_counter() - t0, 1)
    return out


def main() -> None:
    token = login()
    #  Làm nóng: lượt đầu dựng cache hồ sơ quyền + nạp mô-đun openpyxl, không tính.
    with httpx.Client(base_url=BASE) as c:
        for p in ENDPOINTS:
            fire(c, p, token)
    results = {}
    for n in LEVELS:
        results[f"{n}x"] = run(n, token)
        r = results[f"{n}x"]
        print(f"{n:>4} người: {r['ok']}/{r['total_calls']} đạt, p50 {r['p50_ms']} ms, p95 {r['p95_ms']} ms, "
              f"max {r['max_ms']} ms, {r['wall_seconds']} s, lỗi {r['error_statuses']}", file=sys.stderr, flush=True)
        time.sleep(3)   # cho bể kết nối nguội giữa hai bậc
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
