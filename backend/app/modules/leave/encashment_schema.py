"""Schema vào cho PHIẾU THANH TOÁN NGHỈ PHÉP (duoc-CR-719). Ô chữ có `max_length`, ngày có dải năm — vượt là 422.

Phiếu CHỈ ghi số ngày: không có trường tiền (số tiền nhập ở YCTT sinh ra sau khi duyệt).
"""
from datetime import date

from pydantic import BaseModel, Field, field_validator

from .constants import LeaveEncashmentReason

ENCASH_DATE_MIN, ENCASH_DATE_MAX = date(2000, 1, 1), date(2100, 12, 31)
_REASON_CODES = {int(r) for r in LeaveEncashmentReason}


def _check_reason(value):
    if value is not None and int(value) not in _REASON_CODES:
        raise ValueError("Lý do thanh toán chỉ nhận 1 (phép dư cuối năm) hoặc 2 (nghỉ việc)")
    return value


class LeaveEncashmentCreate(BaseModel):
    #  0 / vắng = chính người đang lập; khác chính mình thì phải qua `ensure_can_create_for`.
    employee_id: int = Field(0, ge=0)
    leave_type_id: int = Field(..., ge=1)
    #  Bỏ trống = năm nay. Service chỉ nhận năm nay hoặc năm trước.
    balance_year: int | None = Field(None, ge=2000, le=2100)
    reason_kind: int = Field(int(LeaveEncashmentReason.YEAR_END))
    encashment_date: date | None = Field(None, ge=ENCASH_DATE_MIN, le=ENCASH_DATE_MAX)
    #  Bỏ trống = lấy đúng số được phép thanh toán lúc lập (ERPNext). Bước 0,5 do service kiểm.
    days: float | None = Field(None, gt=0, le=366)
    note: str = Field("", max_length=1000)

    _reason = field_validator("reason_kind")(_check_reason)


class LeaveEncashmentUpdate(BaseModel):
    """Sửa phiếu Nháp / Trả về. Không đổi người nhận, loại nghỉ, năm quỹ — muốn đổi thì xóa lập lại."""

    reason_kind: int | None = None
    encashment_date: date | None = Field(None, ge=ENCASH_DATE_MIN, le=ENCASH_DATE_MAX)
    days: float | None = Field(None, gt=0, le=366)
    note: str | None = Field(None, max_length=1000)

    _reason = field_validator("reason_kind")(_check_reason)
