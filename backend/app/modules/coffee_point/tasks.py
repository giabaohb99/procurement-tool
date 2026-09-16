"""Task Celery của Điểm cà phê — 5 vòng đồng bộ, mỗi lần chạy một dòng nhật ký.

Lịch beat khai ở `core/celery_app.py`. Mọi task đều:
  1. mở một dòng LƯỢT CHẠY trong quyển sổ chung `tab_sync_log` (nguồn `pos365`,
     `grain = RUN`, trạng thái *đang chạy*) — "quán kêu thiếu điểm là tra ra
     trong một phút" (D-05);
  2. chạy nghiệp vụ ở `service.py` (client mock được ở test);
  3. đóng dòng: thành công / lỗi / bỏ qua. `Pos365Disabled` (cầu dao HARD_OFF) là
     *bỏ qua* — chủ ý, không phải sự cố, KHÔNG tính vào chuỗi cảnh báo D-06.

⚠️ Bảng riêng `tab_pos_sync_run` đã bỏ; mọi thứ nay đi qua
`modules/sync_log/service.py`. Ai thêm hệ ngoài mới cũng dùng đúng ba hàm
`open_run` / `finish_run` / `recent_runs` này, đừng đẻ bảng nhật ký mới.

Cảnh báo D-06: một loại task lỗi 3 lần LIÊN TIẾP → chuông cho vai trò
`coffee_admin`. Không có lần đồng bộ nào chết im lặng.
"""
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.sync_log.constants import SyncStatus
from app.modules.sync_log.registry import SOURCE_POS365
from app.modules.sync_log.service import finish_run, open_run, recent_runs

from . import service
from .model import ENUM_LABELS, SYNC_JOB_BY_KIND, PosSyncKind
from .pos365_client import Pos365Disabled, get_client

log = logging.getLogger("app.coffee_point.tasks")

FAIL_ALERT_STREAK = 3


def _alert_failures(db, job: str, label: str):
    """Chuỗi lỗi liên tiếp của một loại task chạm ngưỡng → chuông `coffee_admin`."""
    recent = recent_runs(db, SOURCE_POS365, job, FAIL_ALERT_STREAK,
                         statuses=(SyncStatus.SUCCESS, SyncStatus.FAILED))
    if len(recent) < FAIL_ALERT_STREAK:
        return
    if any(r.status != int(SyncStatus.FAILED) for r in recent):
        return
    try:
        from app.modules.notification.model import Notification
        from app.modules.notification.service import get_users_by_role_codes
        for u in get_users_by_role_codes(db, ["coffee_admin"]):
            db.add(Notification(
                user_id=u.id,
                title=f"Đồng bộ POS365 lỗi liên tiếp: {label}",
                body=f"Tác vụ '{label}' đã lỗi {FAIL_ALERT_STREAK} lần liên tiếp — "
                     "mở Sổ điểm & đối soát › Nhật ký đồng bộ để xem chi tiết.",
                link="/dego-coffee/ledger",
            ))
        db.commit()
    except Exception:  # noqa: BLE001 — cảnh báo là best-effort, không được giết task
        log.exception("Không gửi được cảnh báo đồng bộ POS365")


def _run_logged(kind: PosSyncKind, fn, actor_id: int = 0) -> dict:
    """Khung chung: mở nhật ký → chạy → đóng nhật ký. `fn(db)` trả dict stats;
    các khóa `fetched/written/skipped/cursor_*` (nếu có) chép vào dòng nhật ký,
    phần còn lại vào `payload` (JSON) cho màn đối soát đọc."""
    job = SYNC_JOB_BY_KIND[kind]
    label = ENUM_LABELS["pos_sync_kind"].get(kind, job)
    db = SessionLocal()
    run = open_run(db, SOURCE_POS365, job, entity="pos_order", user_id=actor_id)
    status, message, stats = SyncStatus.SUCCESS, "", {}
    try:
        stats = fn(db) or {}
        return {"status": "success", "run_id": run.id}
    except Pos365Disabled as e:
        db.rollback()
        status, message = SyncStatus.SKIPPED, f"Cầu dao HARD_OFF đang bật: {e}"
        return {"status": "skipped", "run_id": run.id}
    except Exception as e:  # noqa: BLE001 — mọi lỗi phải thành một dòng sổ trạng thái lỗi
        db.rollback()
        status, message = SyncStatus.FAILED, str(e)[:2000]
        log.exception("Đồng bộ POS365 lỗi (%s)", kind.name)
        return {"status": "failed", "run_id": run.id, "error": str(e)[:200]}
    finally:
        #  `stats` là dict do nghiệp vụ trả; bóc ra năm khóa có cột riêng, phần
        #  còn lại giữ nguyên trong `payload`.
        detail = dict(stats)
        finish_run(
            db, run, status, message=message,
            fetched=int(detail.pop("fetched", 0) or 0),
            written=int(detail.pop("written", 0) or 0),
            skipped=int(detail.pop("skipped", 0) or 0),
            cursor_from=str(detail.pop("cursor_from", "") or ""),
            cursor_to=str(detail.pop("cursor_to", "") or ""),
            detail=detail or None,
        )
        if status == SyncStatus.FAILED:
            _alert_failures(db, job, label)
        db.close()


@celery_app.task(name="coffee.pull_orders")
def pull_orders_task(actor_id: int = 0) -> dict:
    client = get_client()
    return _run_logged(PosSyncKind.PULL_ORDERS,
                       lambda db: service.run_pull_orders(db, client, actor_id), actor_id)


@celery_app.task(name="coffee.check_voids")
def check_voids_task(actor_id: int = 0) -> dict:
    client = get_client()
    return _run_logged(PosSyncKind.CHECK_VOIDS,
                       lambda db: service.run_check_voids(db, client, actor_id), actor_id)


@celery_app.task(name="coffee.monthly_reset")
def monthly_reset_task(period: str | None = None, actor_id: int = 0) -> dict:
    """A-06 (chốt 08/09/2026): cấp phát từng kỳ PHẢI CÓ NGƯỜI DUYỆT — beat ngày 1
    KHÔNG tự cấp nữa, chỉ chạy DỰ KIẾN + bắn chuông nhắc `coffee_admin` vào chốt
    (`POST /api/coffee/reset/execute`, quyền `coffee_ledger.approve`)."""

    def _remind(db):
        stats = service.run_monthly_reset(db, period, actor_id=actor_id, dry_run=True)
        cho_cap = [r for r in stats["preview"] if not r["already_granted"]]
        if cho_cap:
            try:
                from app.modules.notification.model import Notification
                from app.modules.notification.service import get_users_by_role_codes
                for u in get_users_by_role_codes(db, ["coffee_admin"]):
                    db.add(Notification(
                        user_id=u.id,
                        title=f"Đến kỳ cấp phát điểm cà phê {stats['period']}",
                        body=f"{len(cho_cap)} người chờ cấp — mở Sổ điểm & đối soát "
                             "để xem bảng dự kiến và CHỐT cấp phát.",
                        link="/dego-coffee/ledger",
                    ))
                db.commit()
            except Exception:  # noqa: BLE001 — chuông là best-effort
                log.exception("Không gửi được chuông nhắc cấp phát")
        return {"fetched": len(stats["preview"]), "written": 0,
                "skipped": len(stats["preview"]) - len(cho_cap),
                "pending_approval": len(cho_cap), "period": stats["period"]}

    return _run_logged(PosSyncKind.MONTHLY_RESET, _remind, actor_id)


@celery_app.task(name="coffee.reconcile")
def reconcile_task(actor_id: int = 0) -> dict:
    return _run_logged(PosSyncKind.RECONCILE,
                       lambda db: service.run_reconcile(db), actor_id)


@celery_app.task(name="coffee.mirror_balance")
def mirror_balance_task(actor_id: int = 0) -> dict:
    """D-07 — chỉ có ích khi POC P5 xác nhận ghi được; chưa bật lịch beat."""
    client = get_client()
    return _run_logged(PosSyncKind.MIRROR,
                       lambda db: service.run_mirror_balance(db, client), actor_id)
