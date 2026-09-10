"""Task Celery của Điểm cà phê — 5 vòng đồng bộ, mỗi lần chạy một dòng nhật ký.

Lịch beat khai ở `core/celery_app.py`. Mọi task đều:
  1. mở dòng `tab_pos_sync_run` (RUNNING) — "quán kêu thiếu điểm là tra ra trong
     một phút" (D-05);
  2. chạy nghiệp vụ ở `service.py` (client mock được ở test);
  3. đóng dòng: SUCCESS / FAILED / SKIPPED. `Pos365Disabled` (cầu dao HARD_OFF) là
     SKIPPED — chủ ý, không phải sự cố, KHÔNG tính vào chuỗi cảnh báo D-06.

Cảnh báo D-06: một loại task FAILED 3 lần LIÊN TIẾP → chuông cho vai trò
`coffee_admin`. Không có lần đồng bộ nào chết im lặng.
"""
import json
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from . import service
from .model import PosSyncKind, PosSyncRun, PosSyncStatus
from .pos365_client import Pos365Disabled, get_client

log = logging.getLogger("app.coffee_point.tasks")

FAIL_ALERT_STREAK = 3


def _alert_failures(db, kind: int):
    """Chuỗi FAILED liên tiếp của một loại task chạm ngưỡng → chuông `coffee_admin`."""
    recent = (db.query(PosSyncRun)
              .filter(PosSyncRun.kind == kind,
                      PosSyncRun.status.in_([int(PosSyncStatus.SUCCESS),
                                             int(PosSyncStatus.FAILED)]))
              .order_by(PosSyncRun.id.desc()).limit(FAIL_ALERT_STREAK).all())
    if len(recent) < FAIL_ALERT_STREAK:
        return
    if any(r.status != int(PosSyncStatus.FAILED) for r in recent):
        return
    try:
        from app.modules.notification.model import Notification
        from app.modules.notification.service import get_users_by_role_codes
        label = recent[0].kind_label
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
    phần còn lại vào `detail` (JSON) cho màn đối soát đọc."""
    db = SessionLocal()
    run = PosSyncRun(kind=int(kind), status=int(PosSyncStatus.RUNNING),
                     started_at=service.now_str(), created_by=actor_id,
                     updated_by=actor_id)
    db.add(run)
    db.commit()
    try:
        stats = fn(db) or {}
        run.fetched = int(stats.pop("fetched", 0))
        run.written = int(stats.pop("written", 0))
        run.skipped = int(stats.pop("skipped", 0))
        run.cursor_from = str(stats.pop("cursor_from", ""))
        run.cursor_to = str(stats.pop("cursor_to", ""))
        if stats:
            run.detail = json.dumps(stats, ensure_ascii=False)[:20000]
        run.status = int(PosSyncStatus.SUCCESS)
        return {"status": "success", "run_id": run.id}
    except Pos365Disabled as e:
        db.rollback()
        run.status = int(PosSyncStatus.SKIPPED)
        run.error = str(e)
        return {"status": "skipped", "run_id": run.id}
    except Exception as e:  # noqa: BLE001 — mọi lỗi phải thành dòng nhật ký FAILED
        db.rollback()
        run.status = int(PosSyncStatus.FAILED)
        run.error = str(e)[:2000]
        log.exception("Đồng bộ POS365 lỗi (%s)", kind.name)
        return {"status": "failed", "run_id": run.id, "error": str(e)[:200]}
    finally:
        run.finished_at = service.now_str()
        db.add(run)
        db.commit()
        if run.status == int(PosSyncStatus.FAILED):
            _alert_failures(db, int(kind))
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
