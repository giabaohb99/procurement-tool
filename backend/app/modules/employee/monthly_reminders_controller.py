"""`GET /api/employees/monthly-reminders?month=YYYY-MM` — dữ liệu ô "Lịch nhắc trong tháng" (E3, duoc-CR-689).

⚠️ Chung tiền tố `/api/employees` với `controller.py` nên router này PHẢI được include TRƯỚC `employee_router`
trong `main.py` — nếu không `monthly-reminders` rơi vào `/{eid}` (422).
Gác `require('employee','read')` + `apply_scope`; sinh nhật cần thêm `employee_sensitive.read`, hợp đồng /
thử việc cần `labor_contract.read` (thiếu quyền thì nhóm đó `allowed=false`, rỗng). `month` sai -> 422.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.core.vn_time import vn_today

from . import monthly_reminders_service as svc
from .model import Employee
from .sensitive import can_read_sensitive

router = APIRouter(prefix="/api/employees", tags=["employee"])
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")


def parse_month(raw: str | None, today) -> tuple[int, int]:
    """`YYYY-MM` -> (năm, tháng); trống = tháng hiện tại; sai định dạng / ngoài 2000-2100 -> 422."""
    if raw is None or not raw.strip():
        return today.year, today.month
    m = _MONTH.match(raw.strip())
    if not m or not (2000 <= int(m.group(1)) <= 2100) or not (1 <= int(m.group(2)) <= 12):
        raise HTTPException(422, "Tháng phải đúng dạng YYYY-MM (ví dụ 2026-10), trong khoảng năm 2000-2100")
    return int(m.group(1)), int(m.group(2))


@router.get("/monthly-reminders")
def monthly_reminders(request: Request, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    today = vn_today()
    year, month = parse_month(request.query_params.get("month"), today)
    prof = get_perm_profile(db, user)
    perms = prof.get("perms_union") or {}
    q = apply_scope(db.query(Employee), Employee, "employee", user, prof)
    return success(svc.build(
        db, q, year=year, month=month, today=today, with_sensitive=can_read_sensitive(prof),
        with_contracts=bool((perms.get("labor_contract") or {}).get("read")), user=user, profile=prof))
