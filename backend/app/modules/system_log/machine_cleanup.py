"""Dọn NHẬT KÝ DO MÁY GHI — bao-CR-731 (người chủ gật 05/11/2026).

Đo prod 05/11/2026: bốn bảng nhật ký máy (request 197 MB, nạp tệp 183 MB, đồng bộ 173 MB, thay đổi 54 MB) là hơn nửa CSDL
~1.020 MB, tăng theo ngày chứ không theo việc kinh doanh. Năm luật, mỗi luật một `Rule`:

| Bảng | Dọn gì | Giữ gì |
|---|---|---|
| `tab_sync_log` | *Bỏ qua* quá 14 ngày, *Thành công* quá 90 ngày | Lỗi / Chờ / Đang chạy giữ mãi; dòng mới nhất mỗi đối tượng (xem dưới) |
| `tab_email_log` | NỘI DUNG thư quá 90 ngày (đặt `html_body = ""`); dòng quá 16 tháng | người nhận, tiêu đề, trạng thái 16 tháng |
| `tab_import_log` | dòng mức Thông tin, `row_status = 0`, quá 30 ngày — mọi loại nạp | Cảnh báo / Cần rà / Lỗi; dòng kết cục từng dòng của lô hải quan (luật riêng `customs.cleanup_row_logs`) |
| `tab_change_log` | mọi dòng của bảng nhật ký máy (`MACHINE_LOG_TABLES`) | — (từ nay không ghi nữa) |
| `tab_request_log` | GET quá 30 ngày — việc riêng `request_log.cleanup`, ở đây chỉ để script đếm chung | dòng ghi 16 tháng |

**Sổ đồng bộ — vì sao giữ "dòng mới nhất mỗi đối tượng".** Ba chỗ đọc ngược sổ, xóa mù là hỏng cả ba:
`is_unchanged` so `content_hash` với dòng THÀNH CÔNG mới nhất của phiếu (mất nó thì lượt quét đêm ghi lại mọi phiếu cũ);
`last_successful_run` lấy con trỏ kéo từ lượt chạy THÀNH CÔNG mới nhất của công việc (mất nó thì kéo lại từ đầu);
`find_stale_failures` coi dòng lỗi là đã vá khi có dòng êm (thành công / bỏ qua) MỚI HƠN cùng đối tượng (mất nó thì chuông
08:00 réo lại lỗi đã vá). Nên giữ: dòng mới nhất mỗi khóa trong nhóm thành công, dòng mới nhất mỗi khóa trong nhóm êm, và
lượt chạy còn được dòng lỗi / chờ trỏ tới qua `run_id`. Khóa = (grain, nguồn, đối tượng, mã bên cũ, công việc).

**Nhật ký thư — vì sao `""` chứ không `NULL`.** `NULL` nghĩa là *không bao giờ lưu* (thư trước bao-CR-727, thư đặt mật
khẩu); `""` nghĩa là *đã lưu rồi dọn*. Hai lý do khác nhau thì câu báo trên nút Gửi lại cũng khác nhau.

Mọi luật xóa / sửa theo lô nhỏ (chọn id rồi `IN`), có trần số lô mỗi lần chạy, và có `dry_run` chỉ đếm.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_policy import CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES, MACHINE_LOG_TABLES

log = logging.getLogger("app.system_log.machine_cleanup")


@dataclass(frozen=True)
class Rule:
    key: str
    table: str
    label: str
    model: object
    condition: Callable[[datetime], object]
    action: str = "delete"          # delete | clear_body
    nightly: bool = True            # False = có việc riêng, ở đây chỉ để đếm / chạy tay


def _days_ago(now: datetime, days: int) -> datetime:
    return now - timedelta(days=max(1, int(days)))


# ---------- tab_sync_log ----------
def _sync_condition(now: datetime):
    from app.modules.sync_log.constants import SyncStatus
    from app.modules.sync_log.model import SyncLog as S

    key = (S.grain, S.source, S.entity, S.legacy_id, S.job)
    success = int(SyncStatus.SUCCESS)
    healed = (success, int(SyncStatus.SKIPPED))
    newest_success = select(func.max(S.id)).where(S.status == success).group_by(*key)
    newest_healed = select(func.max(S.id)).where(S.status.in_(healed)).group_by(*key)
    open_runs = select(S.run_id).where(
        S.status.in_((int(SyncStatus.FAILED), int(SyncStatus.PENDING), int(SyncStatus.RUNNING))), S.run_id != 0)
    #  MySQL không cho subquery trên CHÍNH bảng đang DELETE — nhưng ở đây chỉ SELECT id (xóa bằng `IN` danh sách id).
    return and_(
        or_(and_(S.status == int(SyncStatus.SKIPPED), S.created_at < _days_ago(now, settings.SYNC_LOG_SKIPPED_KEEP_DAYS)),
            and_(S.status == success, S.created_at < _days_ago(now, settings.SYNC_LOG_SUCCESS_KEEP_DAYS))),
        S.id.notin_(newest_success), S.id.notin_(newest_healed), S.id.notin_(open_runs))


# ---------- tab_email_log ----------
def _email_body_condition(now: datetime):
    from app.modules.notification.model import EmailLog as E
    return and_(E.html_body.isnot(None), E.html_body != "", E.created_at < _days_ago(now, settings.EMAIL_BODY_KEEP_DAYS))


def _email_row_condition(now: datetime):
    from app.modules.notification.model import EmailLog as E

    from .retention import retention_cutoff
    return E.created_at < retention_cutoff(now)


# ---------- tab_import_log ----------
def _import_info_condition(now: datetime):
    from app.modules.import_tool.model import ImportLog as L
    from app.modules.import_tool.model import LogLevel
    #  `row_status = 0`: dòng nhật ký thường. Dòng kết cục từng dòng của lô hải quan (row_status ≠ 0) có luật riêng
    #  (bao-CR-698: Ghi đè / Xóa / Bỏ qua / Thêm mới cần rà giữ vĩnh viễn) — không đụng ở đây.
    return and_(L.level == int(LogLevel.INFO), L.row_status == 0,
                L.created_at < _days_ago(now, settings.IMPORT_INFO_LOG_KEEP_DAYS))


# ---------- tab_change_log ----------
def _change_machine_condition(now: datetime):
    from app.modules.change_log.model import ChangeLog as C
    return C.table_name.in_(sorted(MACHINE_LOG_TABLES))


# ---------- tab_request_log (việc riêng) ----------
def _request_get_condition(now: datetime):
    from app.modules.request_log.model import RequestLog as R
    from app.modules.request_log.tasks import get_cutoff
    return and_(R.method == "GET", R.created_at < get_cutoff(now))


def _models():
    from app.modules.change_log.model import ChangeLog
    from app.modules.import_tool.model import ImportLog
    from app.modules.notification.model import EmailLog
    from app.modules.request_log.model import RequestLog
    from app.modules.sync_log.model import SyncLog
    return SyncLog, EmailLog, ImportLog, ChangeLog, RequestLog


def rules() -> list[Rule]:
    sync, email, imp, change, request = _models()
    return [
        Rule("sync_log", "tab_sync_log", "Sổ đồng bộ: Bỏ qua quá "
             f"{settings.SYNC_LOG_SKIPPED_KEEP_DAYS} ngày, Thành công quá {settings.SYNC_LOG_SUCCESS_KEEP_DAYS} ngày",
             sync, _sync_condition),
        Rule("email_body", "tab_email_log", f"Nhật ký thư: nội dung quá {settings.EMAIL_BODY_KEEP_DAYS} ngày",
             email, _email_body_condition, action="clear_body"),
        Rule("email_row", "tab_email_log", "Nhật ký thư: dòng quá 16 tháng", email, _email_row_condition),
        Rule("import_info", "tab_import_log",
             f"Nhật ký nạp tệp: dòng Thông tin quá {settings.IMPORT_INFO_LOG_KEEP_DAYS} ngày", imp, _import_info_condition),
        Rule("change_machine", "tab_change_log", "Nhật ký thay đổi của bảng nhật ký máy", change,
             _change_machine_condition),
        Rule("request_get", "tab_request_log", f"Nhật ký request: GET quá {settings.REQUEST_LOG_GET_KEEP_DAYS} ngày",
             request, _request_get_condition, nightly=False),
    ]


def count(db: Session, rule: Rule, now: datetime) -> int:
    return int(db.execute(select(func.count()).select_from(rule.model).where(rule.condition(now))).scalar() or 0)


def apply(db: Session, rule: Rule, now: datetime, budget: int = CLEANUP_MAX_BATCHES) -> tuple[int, bool]:
    """Chạy một luật theo lô. Trả (số dòng đã xử lý, có chạm trần số lô không)."""
    model, condition = rule.model, rule.condition(now)
    done = batches = 0
    while batches < budget:
        ids = [r[0] for r in db.execute(select(model.id).where(condition).order_by(model.id.asc())
                                        .limit(CLEANUP_BATCH_SIZE))]
        if not ids:
            return done, False
        if rule.action == "clear_body":
            db.execute(update(model).where(model.id.in_(ids)).values(html_body="")
                       .execution_options(synchronize_session=False))
        else:
            db.execute(delete(model).where(model.id.in_(ids)).execution_options(synchronize_session=False))
        db.commit()
        done += len(ids)
        batches += 1
    log.warning("Dọn %s chạm trần %s lô, lần sau dọn tiếp.", rule.key, budget)
    return done, True


def run(db: Session, *, now: datetime | None = None, dry_run: bool = False, include_all: bool = False,
        only: set[str] | None = None) -> dict:
    """Chạy (hoặc đếm) các luật. `include_all` = cả luật có việc riêng (GET request_log) — script dùng.

    Luật GET chỉ chạy khi R2 đã nối (cùng chốt `request_log.cleanup`: chỉ xóa thứ đã có bản sao ngoài máy).
    """
    from app.core.storage import is_remote_storage_ready

    now = now or datetime.now()
    out = []
    for rule in rules():
        if only and rule.key not in only:
            continue
        if not (rule.nightly or include_all):
            continue
        if rule.key == "request_get" and not dry_run and not is_remote_storage_ready():
            out.append({"key": rule.key, "table": rule.table, "label": rule.label, "rows": 0, "status": "skipped",
                        "reason": "no_remote_archive"})
            continue
        if dry_run:
            out.append({"key": rule.key, "table": rule.table, "label": rule.label, "rows": count(db, rule, now)})
            continue
        done, capped = apply(db, rule, now)
        out.append({"key": rule.key, "table": rule.table, "label": rule.label, "rows": done,
                    "status": "partial" if capped else "success"})
        log.info("Dọn nhật ký máy %s: %s dòng.", rule.key, done)
    return {"status": "dry_run" if dry_run else "done", "now": now.isoformat(timespec="seconds"), "rules": out,
            "total": sum(r["rows"] for r in out)}
