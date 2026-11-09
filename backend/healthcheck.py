"""Healthcheck cho container Docker — bao-CR-735 chống treo prod.

Docker gọi tệp này định kỳ (khai `healthcheck:` trong docker-compose); thoát 0 = khỏe, 1 = hỏng. Hỏng liền
`retries` lần thì container thành `unhealthy` và bộ tự chữa trên máy chủ (`scripts/ops/autoheal.sh`) khởi động lại.
Chỉ dùng thư viện chuẩn + celery có sẵn trong image, KHÔNG nạp app (mỗi lượt kiểm phải nhẹ).

    python healthcheck.py api                  # GET http://127.0.0.1:8000/api/health
    python healthcheck.py celery [tiền-tố]     # ping đúng worker của container này qua Redis

Lúc container mới lên, `start.prod.sh` / `start.agent.sh` còn chạy migration + seed (có khi vài phút) — khi đó
tiến trình số 1 chưa phải uvicorn và lượt kiểm báo KHỎE, để một migration dài không bị giết giữa chừng.
"""
from __future__ import annotations

import os
import socket
import sys
import urllib.request

API_URL = "http://127.0.0.1:8000/api/health"
HTTP_TIMEOUT = 8
PING_TIMEOUT = 8


def main_process_cmdline(path: str = "/proc/1/cmdline") -> str:
    try:
        with open(path, "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""


def api_starting(cmdline: str) -> bool:
    """Tiến trình 1 còn là script khởi động (chưa `exec uvicorn`) → đang migration / seed, chưa xét."""
    return "uvicorn" not in cmdline


def check_api(url: str = API_URL, cmdline: str | None = None) -> tuple[bool, str]:
    if api_starting(main_process_cmdline() if cmdline is None else cmdline):
        return True, "đang khởi động (migration/seed) — chưa xét"
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as resp:
            body = resp.read(512)
            if resp.status == 200 and b'"success":true' in body.replace(b" ", b""):
                return True, "ok"
            return False, f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001 — mọi lỗi đều là hỏng
        return False, f"{type(exc).__name__}: {exc}"


def worker_name(prefix: str = "celery", host: str | None = None) -> str:
    return f"{prefix}@{host or socket.gethostname()}"


def check_celery(prefix: str = "celery") -> tuple[bool, str]:
    from celery import Celery  # chỉ nạp celery, không nạp app.core.celery_app

    name = worker_name(prefix)
    app = Celery(broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    try:
        replies = app.control.ping(destination=[name], timeout=PING_TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        app.close()
    if any(name in reply for reply in replies or []):
        return True, "ok"
    return False, f"{name} không trả lời ping trong {PING_TIMEOUT} giây"


def main(argv: list[str]) -> int:
    kind = argv[1] if len(argv) > 1 else "api"
    if kind == "api":
        ok, why = check_api()
    elif kind == "celery":
        ok, why = check_celery(argv[2] if len(argv) > 2 else "celery")
    else:
        ok, why = False, f"không biết loại kiểm '{kind}'"
    print(why)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
