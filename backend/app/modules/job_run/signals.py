"""Ghi sổ việc chạy ngầm bằng tín hiệu Celery (bao-CR-703).

task_prerun → chèn dòng "Đang chạy"; task_postrun → giờ xong, thời lượng, kết cục, tóm tắt kết quả; task_failure → câu
lỗi. Mọi lỗi khi ghi sổ chỉ log cảnh báo — KHÔNG được làm hỏng task. Mỗi lần ghi một phiên DB riêng, commit ngay.

Không nối ở tiến trình DỊCH VỤ AI tách riêng (AGENT_MODE=service): DB của nó không có bảng này (xem celery_app.py).
"""
import json
import logging
from datetime import datetime

from celery.signals import task_failure, task_postrun, task_prerun

from app.core.job_run_codes import JobRunStatus

log = logging.getLogger("app.job_run.signals")

MAX_TEXT = 2000
SKIP_WORDS = ("skipped", "disabled")
#  Task ghi sổ của chính nó không cần ghi (vòng lặp vô ích); task gỡ lỗi cũng vậy.
IGNORED = frozenset({"debug.ping"})


def _session():
    from app.core.database import SessionLocal

    return SessionLocal()


def _open():
    """Phiên ghi sổ; không mở được (DB sập, chưa cấu hình) thì None — sổ hỏng không được làm hỏng task."""
    try:
        return _session()
    except Exception:  # noqa: BLE001
        log.warning("job_run: không mở được phiên ghi sổ", exc_info=True)
        return None


def _summary(retval) -> str:
    if retval is None:
        return ""
    try:
        text = json.dumps(retval, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(retval)
    return text[:MAX_TEXT]


def outcome(state: str | None, retval) -> int:
    """Kết cục từ trạng thái Celery + giá trị trả về: dict có status skipped / disabled → Bỏ qua; failed → Lỗi."""
    if state and state != "SUCCESS":
        return int(JobRunStatus.FAILED)
    if isinstance(retval, dict):
        st = str(retval.get("status") or "").lower()
        if st in SKIP_WORDS:
            return int(JobRunStatus.SKIPPED)
        if st == "failed":
            return int(JobRunStatus.FAILED)
    return int(JobRunStatus.SUCCESS)


def record_start(task_name: str, task_id: str, worker: str = "") -> None:
    from .model import JobRun

    if task_name in IGNORED:
        return
    db = _open()
    if db is None:
        return
    try:
        db.add(JobRun(task_name=task_name[:120], task_id=(task_id or "")[:64], started_at=datetime.now(),
                      status=int(JobRunStatus.RUNNING), worker=(worker or "")[:120]))
        db.commit()
    except Exception:  # noqa: BLE001 — sổ hỏng không được làm hỏng task
        db.rollback()
        log.warning("job_run: không ghi được lúc bắt đầu %s", task_name, exc_info=True)
    finally:
        db.close()


def record_end(task_name: str, task_id: str, state: str | None, retval) -> None:
    from .model import JobRun

    if task_name in IGNORED:
        return
    db = _open()
    if db is None:
        return
    try:
        row = (db.query(JobRun).filter(JobRun.task_id == (task_id or "")[:64], JobRun.task_name == task_name[:120])
               .order_by(JobRun.id.desc()).first())
        now = datetime.now()
        if row is None:            # không thấy dòng bắt đầu (bật sổ giữa chừng) → ghi một dòng đủ
            row = JobRun(task_name=task_name[:120], task_id=(task_id or "")[:64], started_at=now)
            db.add(row)
        row.finished_at = now
        row.duration_ms = max(0, int((now - row.started_at).total_seconds() * 1000)) if row.started_at else 0
        row.status = outcome(state, retval)
        if row.status == int(JobRunStatus.FAILED) and not row.error:
            row.error = (str(retval) if not isinstance(retval, dict) else str(retval.get("error") or ""))[:MAX_TEXT]
        row.result_summary = "" if row.status == int(JobRunStatus.FAILED) and not isinstance(retval, dict) \
            else _summary(retval)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.warning("job_run: không ghi được lúc xong %s", task_name, exc_info=True)
    finally:
        db.close()


def record_error(task_name: str, task_id: str, exc) -> None:
    from .model import JobRun

    if task_name in IGNORED:
        return
    db = _open()
    if db is None:
        return
    try:
        row = (db.query(JobRun).filter(JobRun.task_id == (task_id or "")[:64]).order_by(JobRun.id.desc()).first())
        if row is not None:
            row.error = f"{type(exc).__name__}: {exc}"[:MAX_TEXT]
            row.status = int(JobRunStatus.FAILED)
            db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.warning("job_run: không ghi được lỗi %s", task_name, exc_info=True)
    finally:
        db.close()


@task_prerun.connect
def _on_prerun(sender=None, task_id=None, task=None, **_kw) -> None:
    worker = getattr(getattr(task, "request", None), "hostname", "") or ""
    record_start(getattr(task, "name", "") or getattr(sender, "name", ""), task_id or "", worker)


@task_postrun.connect
def _on_postrun(sender=None, task_id=None, task=None, retval=None, state=None, **_kw) -> None:
    record_end(getattr(task, "name", "") or getattr(sender, "name", ""), task_id or "", state, retval)


@task_failure.connect
def _on_failure(sender=None, task_id=None, exception=None, **_kw) -> None:
    record_error(getattr(sender, "name", ""), task_id or "", exception)
