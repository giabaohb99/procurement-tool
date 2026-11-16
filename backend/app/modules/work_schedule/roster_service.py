""""AI LÀM / AI NGHỈ" — dựng lưới nhân sự × ngày cho màn Lịch làm việc dạng lịch (phase 07).

⚠️ SỐ TRUY VẤN CỐ ĐỊNH, không phụ thuộc số người × số ngày: đếm + trang nhân sự (2) · dòng
gán lịch · ngày của mẫu · tên mẫu · ca xếp theo ngày (4, `resolver_many`) · ngày lễ (1) · đơn nghỉ kèm tên loại (1) ·
đơn giữ ngày + khoảng cho cờ `leave_hold` (2).

duoc-CR-761: ô của ngày XẾP CA mang `is_shift = true` + `shift` (các khung giờ, tổng giờ, ghi chú, ngày nghỉ do xếp ca);
ô theo mẫu lịch tuần mang `is_shift = false`, `shift = null`. Mọi ô mang `leave_hold` (duoc-CR-761): ngày đó đang có đơn nghỉ
chờ duyệt / đã duyệt của người này nên KHÔNG xếp / đổi ca được (cùng luật `shift_leave_conflicts`, kể cả ngày lễ / ngày nghỉ,
không lọc phạm vi `leave_request`, không lộ mã đơn) — thêm 2 truy vấn cố định (đơn + khoảng).
Mọi phép tính từng ô sau đó là bộ nhớ thuần.

Phạm vi theo HAI lớp độc lập: hàng = người `roster_visibility` cho xem (Nhân sự: phạm vi `employee`; Trưởng phòng: phạm vi
`work_schedule_personal` + mình; còn lại: chỉ mình); lớp nghỉ phép chỉ
lấy đơn nằm trong `apply_scope(LeaveRequest, 'leave_request')` — thấy người không có nghĩa là
thấy được đơn nghỉ của người đó (đơn có thể mang lý do riêng tư); đơn ngoài tầm → ô hiện như
ngày làm bình thường theo lịch.
"""
from datetime import time, timedelta

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.holiday_calendar import holiday_names_many

from .day_rules import day_hours, segment_label, shift_spec
from .resolver_many import load_day_plans_many
from .roster_leave import leave_cell, load_leaves
from .roster_visibility import apply_visible_employees
from .shift_leave_conflicts import held_days
from .shift_loader import SHIFT_SCHEDULE_NAME

MAX_ROSTER_DAYS = 42
STATUS_RESIGNED = "resigned"   # = employee.service.STATUS_RESIGNED (không import để khỏi vòng)


def _hhmm(v: time | None) -> str | None:
    return v.strftime("%H:%M") if v else None


def shift_cell_info(rec) -> dict:
    """Khối `shift` của một ô ngày xếp ca: `segments` dạng "HH:MM–HH:MM", `ranges` = [[giờ đầu, giờ cuối], …] cho hộp xếp
    ca, `hours` = tổng giờ, `is_day_off` = ngày nghỉ do xếp ca (không khung)."""
    spec = shift_spec(rec.segments)
    return {"segments": [segment_label(seg) for seg in rec.segments], "ranges": [list(seg) for seg in rec.segments],
            "hours": day_hours(spec), "note": rec.note, "is_day_off": not rec.segments}


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _employee_page(db: Session, user, profile: dict, p: dict):
    """(tổng, [(Employee, tên phòng)]) — người CHƯA nghỉ việc trước `from_date` và đã vào làm
    không muộn hơn `to_date`.

    `resign_date` đã khai thì NÓ quyết định (còn làm tới ngày đó, kể cả khi HR đã đặt trạng thái
    "đã nghỉ" sớm để khóa hồ sơ). Chưa khai `resign_date` mới dựa vào `status`/`is_active`.
    `hire_date` rỗng = không biết → vẫn liệt kê.
    """
    q = (db.query(Employee, Department.name)
         .outerjoin(Department, Department.id == Employee.department_id)
         .filter(or_(and_(Employee.resign_date.isnot(None), Employee.resign_date >= p["from_date"]),
                     and_(Employee.resign_date.is_(None), Employee.is_active.is_(True),
                          func.coalesce(Employee.status, "") != STATUS_RESIGNED)),
                 or_(Employee.hire_date.is_(None), Employee.hire_date <= p["to_date"])))
    if p["company_id"]:
        q = q.filter(Employee.company_id == p["company_id"])
    if p["department_id"]:
        q = q.filter(Employee.department_id == p["department_id"])
    if p["q"]:
        like = f"%{_escape_like(p['q'])}%"
        q = q.filter(or_(Employee.code.like(like, escape="\\"),
                         Employee.full_name.like(like, escape="\\")))
    q = apply_visible_employees(q, db, user, profile)
    total = q.count()
    rows = (q.order_by(func.coalesce(Department.name, ""), Employee.full_name, Employee.id)
            .offset((p["page"] - 1) * p["page_size"]).limit(p["page_size"]).all())
    return total, rows


def build_roster(db: Session, user, profile: dict, p: dict) -> dict:
    """`p`: from_date, to_date, company_id, department_id, q, page, page_size (đã kiểm ở controller)."""
    total, rows = _employee_page(db, user, profile, p)
    emps = [e for e, _ in rows]
    days = [p["from_date"] + timedelta(days=i) for i in range((p["to_date"] - p["from_date"]).days + 1)]
    plans = load_day_plans_many(db, emps, p["from_date"], p["to_date"])
    holidays = (holiday_names_many(db, {int(e.company_id or 0) for e in emps} | {0},
                                   p["from_date"], p["to_date"]))
    leaves = load_leaves(db, user, profile, [e.id for e in emps], p)
    held = held_days(db, [e.id for e in emps], p["from_date"], p["to_date"])

    shared = holidays[0]   # tiêu đề cột CHỈ mang lễ chung; lễ riêng đi theo từng ô (`holiday_name`)

    items = []
    for emp, dept_name in rows:
        mine_holidays = holidays.get(int(emp.company_id or 0), holidays[0])
        cells = []
        for d in days:
            spec, sched_id = plans.at(emp.id, d)
            rec = plans.shift_at(emp.id, d)
            holiday_name = mine_holidays.get(d)
            is_holiday = holiday_name is not None
            if rec is None:
                start_time, end_time, schedule_name = _hhmm(spec.start), _hhmm(spec.end), plans.name_of(sched_id)
            else:   # ngày xếp ca: giờ vào = đầu khung đầu, giờ ra = cuối khung cuối (24 → "24:00")
                start_time = f"{rec.segments[0][0]:02d}:00" if rec.segments else None
                end_time = f"{rec.segments[-1][1]:02d}:00" if rec.segments else None
                schedule_name = SHIFT_SCHEDULE_NAME
            cells.append({
                "date": d.isoformat(), "work_kind": int(spec.kind),
                "start_time": start_time, "end_time": end_time,
                "schedule_name": schedule_name, "is_holiday": is_holiday,
                "holiday_name": holiday_name or "",
                "is_shift": rec is not None, "shift": shift_cell_info(rec) if rec is not None else None,
                "leave_hold": (emp.id, d) in held,
                "leave": leave_cell(leaves.get(emp.id), d, spec, is_holiday)})
        items.append({"employee_id": emp.id, "code": emp.code, "full_name": emp.full_name,
                      "department_id": int(emp.department_id or 0),
                      "department_name": dept_name or "", "cells": cells})
    return {"from_date": p["from_date"].isoformat(), "to_date": p["to_date"].isoformat(),
            "days": [{"date": d.isoformat(), "weekday": d.weekday(), "holiday_name": shared.get(d, "")}
                     for d in days],
            "total": total, "items": items}
