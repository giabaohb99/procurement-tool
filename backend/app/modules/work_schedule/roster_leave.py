"""LỚP NGHỈ PHÉP của «Ai làm / ai nghỉ» — tách khỏi `roster_service.py` cho gọn tệp.

Phạm vi: chỉ lấy đơn nằm trong `apply_scope(LeaveRequest, 'leave_request')` — thấy người không
có nghĩa là thấy được đơn nghỉ của người đó (đơn có thể mang lý do riêng tư).
"""
from datetime import date, time

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (HOLDING_STATUSES, LEAVE_REQUEST_STATUS_LABELS, LR_APPROVED,
                                         SESSION_HOURLY)
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave.workday_service import leave_mask

from .day_rules import AM, PM, DaySpec, work_mask

_LUNCH_START, _LUNCH_END = time(12, 0), time(13, 0)   # lịch chưa khai giờ nghỉ trưa → mốc chuẩn


def _hourly_window(req: LeaveRequest, day: date, spec: DaySpec) -> tuple[time, time]:
    """Khoảng giờ [lo, hi] của đơn THEO GIỜ trên `day`: ngày đầu từ `from_time` tới hết giờ làm,
    ngày cuối từ đầu giờ làm tới `to_time`, ngày giữa cả ngày; một ngày duy nhất = [from, to]."""
    lo = req.from_time if day == req.from_date else spec.start
    hi = req.to_time if day == req.to_date else spec.end
    return max(lo, spec.start), min(hi, spec.end)   # cắt theo khung giờ làm: 17:30–19:00 không tô gì


def leave_mask_on(req: LeaveRequest, day: date, spec: DaySpec) -> int:
    """Nửa buổi nào của `day` bị đơn này chiếm. Nghỉ THEO GIỜ: so khoảng giờ của riêng ngày đó
    với mốc nghỉ trưa của lịch (`leave_mask` coi buổi `HOURLY` là cả ngày — sai với «khám 9–10h»).
    Chạm đúng mốc trưa (12–13h) không tô nửa nào."""
    if req.from_session == SESSION_HOURLY and req.from_time and req.to_time:
        if spec.start is None or spec.end is None:
            return 0
        lo, hi = _hourly_window(req, day, spec)
        if hi <= lo:
            return 0
        lunch_start, lunch_end = spec.lunch_start or _LUNCH_START, spec.lunch_end or _LUNCH_END
        am = lo < lunch_start and hi > spec.start
        pm = hi > lunch_end and lo < spec.end
        return (AM if am else 0) | (PM if pm else 0)
    return leave_mask(day, req.from_date, req.to_date, req.from_session, req.to_session)


def load_leaves(db: Session, user, profile: dict, emp_ids: list[int], p: dict):
    """`{employee_id: [(đơn, tên loại chính)]}` — đã qua phạm vi `leave_request`."""
    if not emp_ids:
        return {}
    q = (db.query(LeaveRequest, LeaveType.name)
         .outerjoin(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
         .filter(LeaveRequest.employee_id.in_(emp_ids), LeaveRequest.is_deleted.is_(False),
                 LeaveRequest.status.in_(HOLDING_STATUSES),
                 LeaveRequest.from_date <= p["to_date"], LeaveRequest.to_date >= p["from_date"]))
    q = apply_scope(q, LeaveRequest, "leave_request", user, profile)
    out: dict[int, list] = {}
    for req, type_name in q.all():
        out.setdefault(req.employee_id, []).append((req, type_name or ""))
    return out


def leave_cell(leaves, day: date, spec: DaySpec, is_holiday: bool):
    """Đơn nghỉ hiển thị cho một ô, hoặc None. Ngày không phải đi làm (CN, lễ) không tô nghỉ.

    Nhiều đơn cùng ngày (vd. xin sáng một đơn, chiều một đơn): cờ sáng/chiều là HỢP của mọi
    đơn khớp (đã duyệt lẫn chờ duyệt) để không sót nửa buổi nào. Đơn ĐẠI DIỆN (mã, loại,
    trạng thái) chọn theo: đã duyệt thắng chờ duyệt, rồi đơn che nhiều nửa buổi hơn, rồi id nhỏ.
    Hệ quả: `is_approved` phản ánh đơn đại diện, không riêng từng nửa buổi."""
    work = work_mask(spec)
    if not leaves or is_holiday or work == 0:
        return None
    best, union = None, 0
    for req, type_name in leaves:
        if not (req.from_date <= day <= req.to_date):
            continue
        mask = leave_mask_on(req, day, spec) & work
        if mask == 0:
            continue
        union |= mask
        key = (req.status != LR_APPROVED, -bin(mask).count("1"), req.id)
        if best is None or key < best[0]:
            best = (key, req, type_name)
    if best is None:
        return None
    _, req, type_name = best
    return {"request_id": req.id, "code": req.code, "leave_type_name": type_name,
            "status": req.status, "status_label": LEAVE_REQUEST_STATUS_LABELS.get(req.status, ""),
            "is_approved": req.status == LR_APPROVED,
            "morning": bool(union & AM), "afternoon": bool(union & PM)}
