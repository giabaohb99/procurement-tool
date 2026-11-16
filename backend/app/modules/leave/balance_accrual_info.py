"""Ba trường "tích phép" trả kèm dòng quỹ của loại MONTHLY_AFTER (duoc-CR-762) — một chỗ dựng cho mọi đường API.

  · `accrual_start_date` — ngày bắt đầu tích (`YYYY-MM-DD`) hoặc `null` (đang thử việc / không biết ngày vào làm).
  · `accrual_status` — `LeaveAccrualStatus` (1–6, xem `constants.py`); nhãn do backend gửi, giao diện không tự gõ nhãn.
  · `accrual_status_label` — nhãn tiếng Việt của mã trên.
Loại nghỉ KHÔNG phải MONTHLY_AFTER, hoặc dòng quỹ của NĂM ĐÃ QUA, thì cả ba là `null`. Nạp GOM: loại nghỉ (1) + hồ sơ (1) + HĐLĐ (1) cho cả danh sách,
và hai truy vấn sau chỉ phát sinh khi có dòng thuộc loại MONTHLY_AFTER.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.vn_time import vn_today

from . import accrual_start_service
from .accrual_start_service import AccrualStart
from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .constants import LEAVE_ACCRUAL_STATUS_LABELS, LeaveAccrualMode, LeaveAccrualStatus

NO_ACCRUAL_INFO = {"accrual_start_date": None, "accrual_status": None, "accrual_status_label": None}


def fields_of(start: AccrualStart, today: date | None = None) -> dict:
    """Ba trường của một người đã có mốc tích (trạng thái tính tại `today`, mặc định hôm nay giờ VN)."""
    status = start.status_at(today)
    return {"accrual_start_date": start.start.isoformat() if start.start else None,
            "accrual_status": status,
            "accrual_status_label": LEAVE_ACCRUAL_STATUS_LABELS[LeaveAccrualStatus(status)]}


def accrual_info_by_employee(db: Session, employee_ids, today: date | None = None) -> dict[int, dict]:
    """`{employee_id: ba trường}` cho các hồ sơ (dùng khi đã biết dòng nào thuộc loại MONTHLY_AFTER)."""
    return {eid: fields_of(s, today)
            for eid, s in accrual_start_service.official_start_map_by_ids(db, employee_ids).items()}


def accrual_info_map(db: Session, rows: list[LeaveBalance]) -> dict[int, dict]:
    """`{balance.id: ba trường}` — luôn có khóa cho MỌI dòng (loại khác MONTHLY_AFTER → `NO_ACCRUAL_INFO`)."""
    if not rows:
        return {}
    after = int(LeaveAccrualMode.MONTHLY_AFTER)
    today = vn_today()
    after_types = {tid for (tid,) in db.query(LeaveType.id).filter(
        LeaveType.id.in_({r.leave_type_id for r in rows}), LeaveType.accrual_mode == after).all()}
    #  Năm đã qua: quỹ đã chốt, không còn "đang tích" nữa → null.
    def shown(r) -> bool:
        return r.leave_type_id in after_types and r.year >= today.year

    wanted = [r for r in rows if shown(r)]
    by_emp = accrual_info_by_employee(db, {r.employee_id for r in wanted}, today) if wanted else {}
    return {r.id: (by_emp.get(r.employee_id, NO_ACCRUAL_INFO) if shown(r) else NO_ACCRUAL_INFO) for r in rows}


