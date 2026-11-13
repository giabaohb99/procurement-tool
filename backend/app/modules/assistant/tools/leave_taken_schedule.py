"""Hai phần dùng chung của tool nghỉ phép (duoc-CR-757): NGÀY ĐÃ NGHỈ theo loại + LỊCH LÀM VIỆC dạng gọn.

Dùng cho `my_leave_summary` (chính người hỏi) và `employee_leave_summary` (nhân sự khác, HR / quản lý) — một chỗ
tính để hai tool không thể nói hai con số khác nhau cho cùng một người.

* **Ngày đã nghỉ** đọc THEO DÒNG loại nghỉ (`tab_leave_request_line`), gồm cả loại KHÔNG trừ quỹ (không lương, ốm...)
  — `used_days` của quỹ phép chỉ có loại trừ quỹ. Năm của một đơn = năm của `from_date`, đúng luật sổ quỹ
  (`leave.request_service.reserve_lines / consume_lines` đều lấy `obj.from_date.year`); đừng đổi sang năm của
  `to_date` hay chia theo ngày thật, không thì "đã nghỉ" lệch với `used_days`.
* **Lịch làm việc** chỉ là cách BÀY lại kết quả của `work_schedule.resolver` — không phân giải lại ở đây.
"""
from datetime import date

from sqlalchemy import case, func

from app.core.vn_time import vn_today
from app.core.work_schedule_codes import WORK_SCHEDULE_LEVEL_LABELS, WorkScheduleLevel
from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine
from app.modules.work_schedule.day_rules import FALLBACK_NAME

WEEKDAY_LABELS = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật")

SCHEDULE_GLOSSARY = (
    "Lịch làm việc đang áp hôm nay: level_label cho biết lịch lấy từ đâu (Nhân sự / Phòng ban / Pháp nhân / Toàn hệ "
    "thống), is_fallback=true là chưa ai gán lịch nên theo mặc định T2–T7 08:00–17:00. Ngày nghỉ phép được ĐẾM theo "
    "lịch có hiệu lực ở từng ngày nghỉ: ngày Nghỉ của lịch và ngày lễ không tính, ngày chỉ làm buổi sáng / buổi chiều "
    "tính tối đa 0.5, nghỉ theo giờ = số giờ nghỉ chia số giờ làm của chính ngày đó. Riêng loại nghỉ tính theo ngày "
    "lịch (vd thai sản) thì đếm cả ngày nghỉ và ngày lễ."
)
TAKEN_GLOSSARY = (
    "taken_by_type = số ngày nghỉ trong năm theo TỪNG loại, gồm cả loại không trừ quỹ (không lương, ốm...): "
    "approved_days là đơn ĐÃ DUYỆT bắt đầu từ hôm nay trở về trước (đã / đang nghỉ), approved_upcoming_days là đơn "
    "đã duyệt cho ngày SẮP TỚI (chưa nghỉ), pending_days là đơn đang chờ duyệt. taken_total_days = tổng approved_days "
    "mọi loại — con số DUY NHẤT để trả lời 'đã nghỉ mấy ngày'; upcoming_total_days là đã duyệt nhưng chưa tới ngày, "
    "nói riêng ra, đừng cộng vào số đã nghỉ. Cả đơn tính vào năm của NGÀY BẮT ĐẦU nghỉ (khớp sổ quỹ phép); báo cáo "
    "Tình hình nghỉ phép chia ngày theo ngày thật nên có thể khác ở đơn vắt qua hai năm."
)
TAKEN_SCOPE_NOTE = (
    " taken_by_type rỗng có thể vì người hỏi không có quyền xem đơn nghỉ phép của người này (phạm vi đơn nghỉ hẹp "
    "hơn phạm vi quỹ phép) — khi đó nói là không xem được, đừng nói người đó chưa nghỉ ngày nào."
)


_TOTALS = {"approved_days": "taken_total_days", "approved_upcoming_days": "upcoming_total_days",
           "pending_days": "pending_total_days"}


def get_year_bounds(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def build_empty_taken(employee_ids) -> dict[int, dict]:
    """Khuôn rỗng của `taken_by_type_many` — dùng cả khi người hỏi không có quyền xem đơn nghỉ."""
    return {int(i): {"taken_by_type": [], **dict.fromkeys(_TOTALS.values(), 0.0)}
            for i in employee_ids if i}


def taken_by_type_many(db, employee_ids, year: int, types: dict[int, dict], *, scope_cond=None,
                       today: date | None = None) -> dict[int, dict]:
    """`{employee_id: {"taken_by_type": [...], "taken_total_days", "upcoming_total_days", "pending_total_days"}}`
    — MỘT truy vấn GROUP BY.

    `types` = danh mục loại nghỉ đã nạp sẵn (`{id: {"name", "code", "counts_balance"}}`) để không tra lại.
    `scope_cond` = điều kiện phạm vi `leave_request` của người hỏi (`scoping.scope_condition`) khi tra NGƯỜI KHÁC —
    dữ liệu này là của đơn nghỉ, không được đi theo phạm vi quỹ phép / hồ sơ (duoc-CR-757 C1). `None` = không lọc
    (chỉ dùng cho chính người hỏi). Đơn đã duyệt tách hai phần theo ngày bắt đầu so với `today` (giờ VN): đã / đang
    nghỉ và sắp tới. Đơn xóa mềm, nháp, từ chối, trả về, đã hủy không tính.
    """
    out = build_empty_taken(employee_ids)
    if not out:
        return out
    lo, hi = get_year_bounds(year)
    upcoming = case((LeaveRequest.from_date > (today or vn_today()), 1), else_=0)
    q = (db.query(LeaveRequest.employee_id, LeaveRequestLine.leave_type_id, LeaveRequest.status, upcoming,
                  func.sum(LeaveRequestLine.days))
         .join(LeaveRequestLine, LeaveRequestLine.request_id == LeaveRequest.id)
         .filter(LeaveRequest.employee_id.in_(sorted(out)), LeaveRequest.is_deleted.is_(False),
                 LeaveRequest.status.in_((LR_APPROVED, LR_PENDING)),
                 LeaveRequest.from_date >= lo, LeaveRequest.from_date <= hi))
    if scope_cond is not None:
        q = q.filter(scope_cond)
    rows = q.group_by(LeaveRequest.employee_id, LeaveRequestLine.leave_type_id, LeaveRequest.status, upcoming).all()
    cells: dict[tuple[int, int], dict] = {}
    for emp_id, type_id, status, is_upcoming, days in rows:
        cell = cells.setdefault((int(emp_id), int(type_id)), dict.fromkeys(_TOTALS, 0.0))
        key = "pending_days" if status == LR_PENDING else ("approved_upcoming_days" if is_upcoming else "approved_days")
        cell[key] += float(days or 0.0)
    for (emp_id, type_id), cell in cells.items():
        info = types.get(type_id) or {}
        item = {"leave_type_id": type_id, "leave_type": info.get("name", ""),
                "leave_type_code": info.get("code", ""), "counts_balance": bool(info.get("counts_balance", False)),
                **{k: round(v, 2) for k, v in cell.items()}}
        bucket = out[emp_id]
        bucket["taken_by_type"].append(item)
        for key, total in _TOTALS.items():
            bucket[total] += item[key]
    for bucket in out.values():
        bucket["taken_by_type"].sort(key=lambda x: x["leave_type"])
        for total in _TOTALS.values():
            bucket[total] = round(bucket[total], 2)
    return out


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def build_schedule_brief(effective: dict) -> dict:
    """Bản GỌN của `resolver.effective_for_employee` cho trợ lý: tên lịch, nguồn, 7 ngày có nhãn thứ."""
    days = []
    for d in effective.get("days") or []:
        day = {"weekday_label": WEEKDAY_LABELS[int(d["weekday"])], "day_kind_label": d.get("day_kind_label", "")}
        if d.get("start_time"):
            day.update(start_time=d["start_time"], end_time=d.get("end_time"))
        if d.get("lunch_start"):
            day.update(lunch_start=d["lunch_start"], lunch_end=d.get("lunch_end"))
        days.append(day)
    return {"schedule_name": effective.get("schedule_name", ""), "is_fallback": bool(effective.get("is_fallback")),
            "level_label": effective.get("level_label", ""), "target_name": effective.get("target_name", ""),
            "effective_from": _iso(effective.get("effective_from")), "effective_to": _iso(effective.get("effective_to")),
            "weekly_workdays": effective.get("weekly_workdays"), "days": days}


def build_schedule_label(plans, employee_id: int, on_date: date) -> dict:
    """Tên lịch + cấp nguồn của một nhân sự từ bản gom `resolver_many.DayPlansMany` (không chạm DB)."""
    hit = plans.winner(employee_id, on_date)
    if hit is None:
        return {"schedule_name": FALLBACK_NAME, "is_fallback": True, "level_label": ""}
    name = plans.names.get(hit.schedule_id)
    if name is None:   # mẫu đã xóa mà dòng gán còn — resolver cũng rơi về mặc định
        return {"schedule_name": FALLBACK_NAME, "is_fallback": True, "level_label": ""}
    level = WorkScheduleLevel(hit.target_level)
    return {"schedule_name": name, "is_fallback": False, "level_label": WORK_SCHEDULE_LEVEL_LABELS[level]}
