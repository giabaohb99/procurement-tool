"""Schema vào cho PHIẾU XIN NGHỈ BÙ (duoc-CR-715 C). Ô chữ có `max_length` — vượt là 422."""
from datetime import date

from pydantic import BaseModel, Field

from app.modules.employee.field_limits import Str1000


#  Dải năm hợp lý của cột ngày (backend-input-limits.md): MySQL nhận tới năm 9999.
WORK_DATE_MIN, WORK_DATE_MAX = date(2000, 1, 1), date(2100, 12, 31)


class LeaveCompRequestCreate(BaseModel):
    #  0 / vắng = chính người đang lập; khác chính mình thì phải qua `ensure_can_create_for`.
    employee_id: int = Field(0, ge=0)
    work_date: date = Field(..., ge=WORK_DATE_MIN, le=WORK_DATE_MAX)
    #  0.5 hoặc 1 — service kiểm lại bằng `COMP_DAYS_ALLOWED`.
    days: float = Field(1.0, gt=0, le=1)
    reason: Str1000 = ""


class LeaveCompRequestUpdate(BaseModel):
    work_date: date | None = Field(None, ge=WORK_DATE_MIN, le=WORK_DATE_MAX)
    days: float | None = Field(None, gt=0, le=1)
    reason: Str1000 | None = None
