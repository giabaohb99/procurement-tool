"""API XẾP CA THEO NGÀY — `/api/work-shifts` (duoc-CR-761).

Trưởng phòng / Nhân sự xếp lại ca theo tiếng cho từng nhân viên từng ngày (có việc làm không liền như livestream nên một
ngày chia nhiều khung); ngày không xếp thì theo mẫu lịch tuần như cũ. CHỈ xếp ca, không chấm công.

Quyền ghi: đường Nhân sự `work_schedule.write|delete` (mọi người trong phạm vi `employee`, mọi ngày) hoặc đường Trưởng
phòng `work_schedule_personal.write|delete` (người trong phạm vi khóa, không phải mình, ngày ≥ hôm nay) — xem `shift_access`.
Ghi hàng loạt kiểm TOÀN BỘ ô trước: sai một ô là không ghi ô nào, lỗi kèm danh sách ô bị từ chối ở `error.details.rejected`.
Mỗi lượt ghi: một dòng nhật ký + một chuông cho mỗi nhân sự bị đổi (không chuông cho người bấm). Không ai tự xếp ca cho
chính mình (trừ quản trị hệ thống); ngày đã có đơn nghỉ chờ duyệt / đã duyệt thì không đổi / gỡ ca (`shift_leave_conflicts`).
"""
from contextlib import contextmanager
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.response import error, success
from app.core.scoping import get_perm_profile
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from . import shift_access as access
from . import shift_service as svc
from .assignment_schema import MAX_ID
from .roster_visibility import apply_visible_employees
from .shift_leave_conflicts import find_leave_conflicts
from .shift_loader import load_shift_records
from .shift_notify import notify_shift_changes
from .shift_schema import MAX_RANGE_DAYS, ShiftBulk, ShiftCopyWeek, ShiftPut, check_year
from .shift_view import build_my_days, employee_of, shift_item

ENTITY = "work_shift"   # tên đối tượng ghi vào nhật ký (không phải khóa quyền)
router = APIRouter(prefix="/api/work-shifts", tags=["work_schedule"])


def _check_range(from_date: date, to_date: date) -> None:
    try:
        check_year(from_date)
        check_year(to_date)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if to_date < from_date:
        raise HTTPException(422, "Đến ngày phải sau hoặc bằng Từ ngày")
    if (to_date - from_date).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(422, f"Chỉ xem tối đa {MAX_RANGE_DAYS} ngày một lần")


def _rejected(rejections: list[access.Rejection]):
    """Phong bì lỗi của ghi hàng loạt: mã HTTP của lý do nặng nhất + danh sách ô bị từ chối (chưa ghi ô nào)."""
    status = access.worst_status(rejections)
    first = next(r for r in rejections if access.REASONS[r.code][0] == status)
    return error(f"Không xếp được {len(rejections)} ô ({first.message}); chưa ghi ô nào",
                 code="shift_rejected", status_code=status,
                 details={"rejected": [r.as_dict() for r in rejections]})


PAST_DELETE_MESSAGE = "Ngày đã qua (hoặc hôm nay) không về mẫu tuần được — sửa khung giờ thay vì xóa"
CONFLICT_MESSAGE = "Ô này vừa được người khác xếp ca, tải lại rồi thử lại"


MYSQL_DEADLOCK, MYSQL_LOCK_WAIT_TIMEOUT = 1213, 1205


def _is_lock_contention(exc: OperationalError) -> bool:
    """Deadlock (1213) hoặc hết chờ khóa (1205) của MySQL — hai lượt xếp ca đụng nhau, không phải lỗi hệ thống."""
    args = getattr(getattr(exc, "orig", None), "args", ()) or ()
    return bool(args) and args[0] in (MYSQL_DEADLOCK, MYSQL_LOCK_WAIT_TIMEOUT)


@contextmanager
def _conflict_guard(db: Session):
    """Hai lượt cùng TẠO / SỬA một ô cùng lúc: UNIQUE `(employee_id, work_date)` làm lượt sau lỗi `IntegrityError` ngay ở
    `flush` của service (không chỉ ở `commit`); hai lượt chạm khóa nhau thì MySQL trả deadlock 1213 / hết chờ khóa 1205
    (`OperationalError`). Cả hai → hoàn tác cả lượt và trả 409 thay vì 500. Lỗi `OperationalError` khác (mất kết nối…) ném tiếp."""
    try:
        yield
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, CONFLICT_MESSAGE) from exc
    except OperationalError as exc:
        if not _is_lock_contention(exc):
            raise
        db.rollback()
        raise HTTPException(409, CONFLICT_MESSAGE) from exc


def _raise_if_leave(db: Session, user, cells) -> None:
    """Đường một ô: ô đang bị đơn nghỉ chờ duyệt / đã duyệt giữ → 409 (kèm mã đơn nếu người gọi xem được đơn)."""
    rejections = _leave_rejections(db, user, cells)
    if rejections:
        raise HTTPException(409, rejections[0].message)


def _leave_rejections(db: Session, user, cells) -> list[access.Rejection]:
    """Các ô đang bị đơn nghỉ chờ duyệt / đã duyệt giữ → danh sách từ chối `leave_conflict`; mã đơn chỉ kèm khi người
    gọi xem được đơn đó theo phạm vi `leave_request` (không thì để rỗng)."""
    found = find_leave_conflicts(db, cells, user, get_perm_profile(db, user))
    return [access.Rejection(emp, day, "leave_conflict", c.request_code, c.status_label)
            for (emp, day), c in sorted(found.items())]


def _span(days: set[date]) -> str:
    first, last = min(days), max(days)
    return f"{first:%d/%m/%Y}" if first == last else f"{first:%d/%m/%Y}–{last:%d/%m/%Y}"


def _finish(db: Session, user, change: svc.ShiftChange, action: str, what: str, entity_id: int = 0):
    """Ghi MỘT dòng nhật ký (cùng giao dịch), commit, rồi báo chuông. Không ô nào đổi → không nhật ký, không chuông."""
    if change.changed:
        all_days = {d for days in change.dates_by_employee.values() for d in days}
        record(db, user.id, ENTITY, entity_id, action,
               f"{what}: {change.changed} ô, {len(change.dates_by_employee)} nhân sự ({_span(all_days)})", commit=False)
    db.commit()
    notify_shift_changes(db, user, change.dates_by_employee)


@router.get("")
def list_shifts(from_date: date, to_date: date, department_id: int = Query(0, ge=0, le=MAX_ID),
                employee_id: int = Query(0, ge=0, le=MAX_ID), db: Session = Depends(get_db),
                user=Depends(require("employee", "read"))):
    """Các ngày XẾP CA (kèm khung giờ) trong khoảng ≤ 42 ngày, lọc theo phòng / nhân sự.

    Quyền: `employee.read`; chỉ trả người `roster_visibility` cho xem: Nhân sự (`work_schedule.write`) = phạm vi `employee`,
    Trưởng phòng (`work_schedule_personal.read`) = người trong phạm vi khóa đó + chính mình, còn lại chỉ chính mình;
    chọn `employee_id` / `department_id` ngoài tập đó thì ra rỗng. Ngày nghỉ do
    xếp ca có `segments` rỗng và `is_day_off = true`. Ngày không có ở đây là ngày theo mẫu lịch tuần.
    """
    _check_range(from_date, to_date)
    profile = get_perm_profile(db, user)
    query = db.query(Employee.id)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if employee_id:
        query = query.filter(Employee.id == employee_id)
    ids = [row.id for row in apply_visible_employees(query, db, user, profile).all()]
    records = load_shift_records(db, ids, from_date, to_date)
    items = [shift_item(records[key]) for key in sorted(records)]
    return success({"from_date": from_date.isoformat(), "to_date": to_date.isoformat(), "items": items})


@router.get("/me")
def my_shifts(from_date: date, to_date: date, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ca làm việc CỦA TÔI từng ngày (≤ 42 ngày): mẫu lịch tuần và ca xếp riêng đã gộp, ca xếp riêng thắng.

    Không cần khóa quyền — ai đăng nhập cũng xem được lịch của chính mình. Tài khoản chưa gắn hồ sơ nhân sự trả
    `employee_id = 0` và danh sách rỗng. Mỗi ngày: `date`, `weekday`, `is_shift`, `work_kind`, `start_time`, `end_time`,
    `segments` ("HH:MM–HH:MM"), `ranges`, `hours`, `note`, `is_day_off`, `is_holiday`, `holiday_name`, `schedule_name`.
    """
    _check_range(from_date, to_date)
    employee = employee_of(db, user)
    return success({"employee_id": int(employee.id) if employee else 0, "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(), "days": build_my_days(db, employee, from_date, to_date)})


@router.put("/{employee_id}/{work_date}")
def put_shift(body: ShiftPut, employee_id: int = Path(ge=1, le=MAX_ID), work_date: date = Path(),
              db: Session = Depends(get_db), user=Depends(access.require_shift_action("write"))):
    """Đặt ca một nhân sự một ngày — THAY cả danh sách khung giờ (rỗng = nghỉ cả ngày do xếp ca).

    Quyền: `work_schedule.write` (mọi ngày) hoặc `work_schedule_personal.write` (người trong phạm vi, từ hôm nay);
    không ai tự xếp cho chính mình (trừ quản trị hệ thống). Lỗi riêng: 400 nhân sự ngoài phạm vi / không tồn tại, 403 tự
    xếp cho mình, 409 ngày đã có đơn nghỉ chờ duyệt / đã duyệt (hoặc trùng lượt), 422 ngày quá khứ (Trưởng phòng) hoặc
    khung sai (tối đa 12 khung, giờ 0–24, không chồng nhau).
    """
    _check_range(work_date, work_date)
    cell = (employee_id, work_date)
    access.raise_for_single(access.check_cells(db, user, get_perm_profile(db, user), "write", [employee_id], [cell]))
    _raise_if_leave(db, user, [cell])
    with _conflict_guard(db):
        change = svc.upsert_items(db, user, [(employee_id, work_date, body.pairs(), body.note)])
        _finish(db, user, change, "update", "Xếp ca", employee_id)
    rec = load_shift_records(db, [employee_id], work_date, work_date)[cell]
    return success(shift_item(rec), "Đã lưu ca")


@router.delete("/{employee_id}/{work_date}")
def delete_shift(employee_id: int = Path(ge=1, le=MAX_ID), work_date: date = Path(),
                 db: Session = Depends(get_db), user=Depends(access.require_shift_action("delete"))):
    """Gỡ ca xếp riêng của một ngày — ngày đó quay về MẪU LỊCH TUẦN. Gỡ ngày không có ca riêng là không làm gì.

    Quyền: `work_schedule.delete` hoặc `work_schedule_personal.delete` (cùng luật phạm vi / tự xếp như đặt ca). Ngày
    hôm nay hoặc đã qua KHÔNG gỡ được (422, kể cả Nhân sự) — sửa khung giờ bằng PUT. Ngày có ca mà đã có đơn nghỉ chờ
    duyệt / đã duyệt → 409. Trả `{deleted: true|false}`.
    """
    _check_range(work_date, work_date)
    if work_date <= vn_today():
        #  Chặn MỌI người kể cả Nhân sự: gỡ ca về mẫu tuần là viết lại ngày đã / đang diễn ra (ngày nghỉ do xếp ca bị gỡ thành
        #  ngày làm, hoặc ngược lại, mở đường xin nghỉ bù). Muốn sửa thì đặt lại khung giờ (PUT), không gỡ.
        raise HTTPException(422, PAST_DELETE_MESSAGE)
    cell = (employee_id, work_date)
    access.raise_for_single(access.check_cells(db, user, get_perm_profile(db, user), "delete", [employee_id], [cell]))
    _raise_if_leave(db, user, svc.existing_cells(db, [cell]))
    with _conflict_guard(db):
        change = svc.delete_cells(db, [cell])
        _finish(db, user, change, "delete", "Gỡ ca về mẫu tuần", employee_id)
    return success({"deleted": bool(change.deleted)}, "Đã gỡ ca" if change.deleted else "Ngày này không có ca riêng")


@router.post("/bulk")
def bulk_shifts(body: ShiftBulk, db: Session = Depends(get_db), user=Depends(access.require_shift_action("write"))):
    """Áp CÙNG một bộ khung giờ cho nhiều nhân sự × nhiều ngày (≤ 50 người, ≤ 42 ngày, ≤ 500 ô một lượt).

    Quyền như đặt ca một ô, kiểm TỪNG ô: sai một ô là không ghi ô nào, mã HTTP là của lý do nặng nhất (403 tự xếp cho
    mình > 400 ngoài phạm vi > 422 ngày quá khứ > 409 đã có đơn nghỉ) và `error.details.rejected` liệt kê ô sai
    (`employee_id`, `work_date`, `code`, `message`, + `request_code` khi `code = leave_conflict`; rỗng nếu người gọi không
    xem được đơn theo phạm vi `leave_request`). Trả `{created, updated,
    changed}`.
    """
    cells = [(emp, day) for emp in body.employee_ids for day in body.dates]
    rejections = access.check_cells(db, user, get_perm_profile(db, user), "write", body.employee_ids, cells)
    rejections = rejections or _leave_rejections(db, user, cells)   # chỉ lộ đơn nghỉ cho người đã đủ quyền xếp ca
    if rejections:
        return _rejected(rejections)
    pairs = body.pairs()
    with _conflict_guard(db):
        change = svc.upsert_items(db, user, [(emp, day, pairs, body.note) for emp, day in cells])
        _finish(db, user, change, "update", "Xếp ca hàng loạt")
    return success({"created": change.created, "updated": change.updated, "changed": change.changed}, "Đã lưu ca")


@router.post("/copy-week")
def copy_week(body: ShiftCopyWeek, db: Session = Depends(get_db),
              user=Depends(access.require_shift_action("write"))):
    """Chép ca của tuần nguồn (thứ Hai) sang tuần đích (thứ Hai) cho các nhân sự đã chọn (≤ 50 người).

    CHỈ chép ngày đã có ca riêng (kể cả ngày nghỉ do xếp ca); ngày theo mẫu tuần không chép. Ngày đích đã có ca thì bỏ
    qua, trừ khi `overwrite = true`. Quyền + lỗi hàng loạt như `/bulk` (kiểm theo các ô ĐÍCH), NGOẠI LỆ: ngày đích đã có đơn
    nghỉ chờ duyệt / đã duyệt thì BỎ QUA (đếm ở `skipped_leave`, liệt kê ở `leave_conflicts` = [{employee_id, work_date,
    request_code}], mã rỗng nếu người gọi không xem được đơn theo phạm vi `leave_request`), và đường Trưởng phòng bỏ qua ngày đích đã qua (`skipped_past`) thay vì từ chối; đường Nhân sự chép cả
    ngày đã qua. Trả `{created, updated, skipped, skipped_past, skipped_leave, leave_conflicts, changed}`.
    """
    plan, skipped = svc.plan_copy_week(db, body.employee_ids, body.source_week_start, body.target_week_start,
                                       body.overwrite)
    #  Đường Trưởng phòng: ngày đích đã qua thì BỎ QUA (đếm vào `skipped_past`) thay vì từ chối cả lượt — chép "tuần trước
    #  sang tuần này" vào giữa tuần là việc thường. Lý do khác (tự xếp cho mình, ngoài phạm vi) vẫn từ chối cả lượt.
    skipped_past = 0
    if not access.holds_hr_key(db, user, "write"):
        today = vn_today()
        kept = [(rec, day) for rec, day in plan if day >= today]
        skipped_past, plan = len(plan) - len(kept), kept
    cells = [(rec.employee_id, day) for rec, day in plan]
    rejections = access.check_cells(db, user, get_perm_profile(db, user), "write", body.employee_ids, cells)
    if rejections:
        return _rejected(rejections)
    conflicts = find_leave_conflicts(db, cells, user, get_perm_profile(db, user))   # ngày đã có đơn nghỉ: bỏ qua, không từ chối cả lượt
    plan = [(rec, day) for rec, day in plan if (rec.employee_id, day) not in conflicts]
    with _conflict_guard(db):
        change = svc.apply_copy_plan(db, user, plan, skipped)
        _finish(db, user, change, "update", "Chép ca tuần")
    notes = [f"bỏ qua {n} ngày {what}" for n, what in ((skipped_past, "đã qua"), (len(conflicts), "đã có đơn nghỉ")) if n]
    message = ("Đã chép ca" if change.changed else "Không có ca nào để chép") + (f" ({', '.join(notes)})" if notes else "")
    return success({"created": change.created, "updated": change.updated, "skipped": change.skipped,
                    "skipped_past": skipped_past, "skipped_leave": len(conflicts),
                    "leave_conflicts": [{"employee_id": emp, "work_date": day.isoformat(), "request_code": c.request_code}
                                        for (emp, day), c in sorted(conflicts.items())],
                    "changed": change.changed}, message)
