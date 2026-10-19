"""Ghép số liệu thành dòng `tab_usage_daily` và ghi idempotent (duoc-CR-641, phase 02).

Mỗi người dùng đang hoạt động (có hồ sơ nhân sự) có MỘT dòng mỗi ngày kể cả khi không vào — thiếu thì mẫu số
«ngày làm việc ròng» sai. Tài khoản không có nhân sự (admin máy) có dòng nếu có hoạt động, lịch = mặc định hệ thống.
Ghi: DELETE các dòng của ngày rồi bulk INSERT (chạy lại không nhân đôi). JSON cắt theo trần để tổng ≤ 16 KB.
"""
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.core.logging_policy import GET_RETENTION_DAYS
from app.core.vn_time import vn_today

from app.modules.employee.service import STATUS_RESIGNED

from .daily_activity import activity_columns
from .daily_docs import audit_columns, login_columns, proxy_columns
from .daily_sources import DaySources, load_day_sources
from .daily_ui import merge_screens, ui_columns
from .daily_window import vn_day_bounds
from .daily_workday import build_calendar
from .model import UsageDaily
from .report_route_keys import report_route_keys

log = logging.getLogger("app.usage_profile.daily")

MAX_JSON_BYTES = 16 * 1024
#  Nguồn thô (GET của request_log, tab_ui_event) bị dọn sau GET_RETENTION_DAYS ngày; ngày cũ hơn mốc này mà gom lại thì
#  DELETE+INSERT sẽ ghi đè số tốt bằng số thiếu (api_reads, hourly, page_views... về 0). Chừa 1 ngày đệm cho job dọn 04:20.
MAX_REAGGREGATE_AGE_DAYS = GET_RETENTION_DAYS - 1
_JSON_COLS = ("hourly", "screens", "docs", "forms", "reports", "forbidden_routes")


def _group(rows: list, key_index: int) -> dict:
    out: dict = defaultdict(list)
    for r in rows:
        out[r[key_index]].append(r)
    return out


def _cap_json(row: dict) -> None:
    """Cắt `screens` (rồi `docs`) cho tới khi tổng các cột JSON ≤ MAX_JSON_BYTES."""
    def size() -> int:
        return sum(len(json.dumps(row[c])) for c in _JSON_COLS if row[c] is not None)

    screens = row["screens"] or {}
    while size() > MAX_JSON_BYTES and screens:
        screens.pop(min(screens, key=lambda k: (screens[k][0], screens[k][2])))
    row["screens"] = screens
    if size() > MAX_JSON_BYTES:
        row["docs"] = {}


def build_rows(src: DaySources, report_map: dict[str, int] | None = None) -> list[dict]:
    day = src.day
    lo, hi = vn_day_bounds(day)
    report_map = report_route_keys() if report_map is None else report_map
    users = {u[0]: u for u in src.users}
    user_emp = {u[0]: u[2] or 0 for u in src.users}
    emp_user = {u[2]: u[0] for u in src.users if u[2]}
    req_by = _group(src.requests, 0)
    ui_by = _group(src.ui_events, 0)
    audit_by = _group(src.audits, 0)
    exp_by = _group(src.exports, 0)
    done, received = proxy_columns(src.proxy_docs, src.approval_proxies, user_emp, emp_user)
    login_users = {s[0] for s in src.sessions.values() if lo <= s[5] < hi}

    wanted = {uid for uid, active, emp, *_ in src.users if active and emp}
    wanted |= set(req_by) | set(ui_by) | set(audit_by) | login_users
    rows: list[dict] = []
    for uid in sorted(wanted & set(users)):
        _, _active, emp_id, company_id, dept_id, emp_status, resign_date = users[uid]
        cal = build_calendar(src.plans, src.holidays, src.leaves, emp_id or 0, company_id or 0, day)
        reqs = [r[1:] for r in req_by.get(uid, [])]
        ui_events = [r[1:] for r in ui_by.get(uid, [])]
        act = activity_columns(reqs, [e[0] for e in ui_events], src.sessions, cal, report_map)
        aud = audit_columns([a[1:] for a in audit_by.get(uid, [])], src.sessions)
        ui = ui_columns(ui_events)
        exports = exp_by.get(uid, [])
        screens = merge_screens(act.pop("_screens_api"), ui.pop("_screens_ui"))
        active = bool(act["active"] or audit_by.get(uid))
        #  Có ngày nghỉ thì chỉ so với NGÀY ĐANG GOM (gom lại ngày trước khi nghỉ không được báo động giả);
        #  `status` hiện tại chỉ là phương án dự phòng khi hồ sơ không có ngày nghỉ.
        resigned = resign_date < day if resign_date else emp_status == STATUS_RESIGNED
        row = {
            "user_id": uid, "day": day, "employee_id": emp_id or 0, "company_id": company_id or 0,
            "department_id": dept_id or 0, "computed_at": datetime.utcnow(),
            "is_workday": cal.is_workday, "is_holiday": cal.is_holiday,
            "work_capacity": cal.work_capacity, "leave_days": cal.leave_days,
            "exports": len(exports), "export_rows": sum(int(e[1] or 0) for e in exports),
            "on_behalf_received": received.get(uid, 0), "on_behalf_done": done.get(uid, 0),
            **act, **aud, **ui, "screens": screens, "active": active,
            **login_columns(uid, src.sessions, lo, hi, src.prior_logins),
            "active_after_resign": resigned and active,
        }
        _cap_json(row)
        rows.append(row)
    return rows


class DayTooOldError(ValueError):
    """Ngày đã quá hạn giữ nguồn thô — gom lại sẽ ghi đè số tốt bằng số thiếu."""


def earliest_safe_day() -> date:
    return vn_today() - timedelta(days=MAX_REAGGREGATE_AGE_DAYS)


def guard_day_age(day: date, force: bool = False) -> None:
    """Từ chối ngày cũ hơn `earliest_safe_day()`; `force=True` bỏ qua nhưng ghi cảnh báo."""
    if day >= earliest_safe_day():
        return
    if not force:
        raise DayTooOldError(
            f"Ngày {day} cũ hơn {MAX_REAGGREGATE_AGE_DAYS} ngày: nguồn thô đã bị dọn, gom lại sẽ ghi đè số cũ bằng số thiếu "
            "(dùng force=True / --force nếu thật sự muốn)")
    log.warning("Gom lại ngày %s NGOÀI hạn giữ nguồn thô (force) — số liệu cũ có thể bị thay bằng số thiếu", day)


def write_rows(db: Session, day: date, rows: list[dict], force: bool = False) -> int:
    """DELETE các dòng của `day` rồi bulk INSERT trong một giao dịch. Từ chối ngày quá hạn giữ nguồn (xem `guard_day_age`)."""
    guard_day_age(day, force)
    db.execute(delete(UsageDaily).where(UsageDaily.day == day))
    if rows:
        db.execute(insert(UsageDaily.__table__), rows)
    db.commit()
    return len(rows)


def aggregate_day(db: Session, day: date, force: bool = False) -> int:
    """Gom MỘT ngày VN cho mọi người dùng; trả số dòng đã ghi. Kiểm tuổi ngày TRƯỚC khi đọc nguồn."""
    guard_day_age(day, force)
    return write_rows(db, day, build_rows(load_day_sources(db, day)), force)
