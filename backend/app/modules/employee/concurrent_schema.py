"""Lược đồ vào/ra cho KIÊM NHIỆM (duoc-CR-755; hai loại dòng ở duoc-CR-756).

Hai loại dòng ĐỘC LẬP (`ConcurrentKind`): **Phòng ban** (chỉ gửi `department_id`; công ty = công ty chính, máy chủ
điền) và **Công ty** (chỉ gửi `company_id` khác công ty chính; không phòng). Hình sai là 422 ngay ở tầng schema;
phần cần đọc hồ sơ (công ty chính, trùng, phục vụ) kiểm ở service.

Khuôn của `work_history_schema.py`: `extra="forbid"`, ô chuỗi có `max_length` khớp cột
(`decision_no` 50, `note` 500 — vượt là 422 chứ không phải 500 của MySQL), ngày trong dải
1900-2100, `to_date >= from_date`. PATCH chỉ cho `to_date` / `decision_date` gửi `null`
tường minh (mở lại / xóa ngày); các ô khác gửi null là 422 kèm tên ô.
"""
from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from app.core.hr_concurrent_codes import ConcurrentKind

from .field_limits import Str50, Str500

#  Dải ngày của kiêm nhiệm hẹp hơn `ProfileDate` (1900-2200): một quyết định bổ nhiệm không
#  có hiệu lực tới năm 2200, gõ nhầm năm là chuyện thường gặp.
ConcurrentDate = Annotated[date, Field(ge=date(1900, 1, 1), le=date(2100, 12, 31))]

ORDER_ERROR = "Đến ngày phải sau hoặc bằng từ ngày"
KIND_DEPARTMENT_NO_COMPANY = "Dòng loại Phòng ban không chọn công ty — công ty là công ty chính của hồ sơ"
KIND_COMPANY_NO_DEPARTMENT = "Dòng loại Công ty không chọn phòng ban"


class ConcurrentIn(BaseModel):
    """Một dòng kiêm nhiệm mới. `from_date` bắt buộc khi tạo mới."""

    model_config = {"extra": "forbid"}

    #  `kind` bắt buộc: 1 Phòng ban, 2 Công ty. Số lạ (0, 3...) là 422.
    kind: ConcurrentKind
    #  Loại 1: `department_id > 0` bắt buộc, `company_id` PHẢI 0/vắng (máy chủ điền công ty chính).
    #  Loại 2: `company_id > 0` bắt buộc (khác công ty chính — kiểm ở service), `department_id` PHẢI 0/vắng.
    company_id: int = Field(0, ge=0)
    department_id: int = Field(0, ge=0)
    position_id: int = Field(0, ge=0)
    from_date: ConcurrentDate
    to_date: ConcurrentDate | None = None
    decision_no: Str50 = ""
    decision_date: ConcurrentDate | None = None
    note: Str500 = ""
    counts_scope: bool = True

    @model_validator(mode="after")
    def _check_date_order(self):
        if self.to_date is not None and self.to_date < self.from_date:
            raise ValueError(ORDER_ERROR)
        return self

    @model_validator(mode="after")
    def _check_shape_by_kind(self):
        if self.kind == ConcurrentKind.DEPARTMENT:
            if self.department_id <= 0:
                raise ValueError("Dòng loại Phòng ban phải chọn phòng ban")
            if self.company_id:
                raise ValueError(KIND_DEPARTMENT_NO_COMPANY)
        else:
            if self.company_id <= 0:
                raise ValueError("Dòng loại Công ty phải chọn công ty")
            if self.department_id:
                raise ValueError(KIND_COMPANY_NO_DEPARTMENT)
        return self


#  Chỉ hai ô này được gửi `null` tường minh trong PATCH (xóa / mở lại).
_NULL_ALLOWED: frozenset[str] = frozenset({"to_date", "decision_date"})


class ConcurrentPatch(BaseModel):
    """Sửa một dòng — mọi ô tùy chọn (PATCH một phần), khóa lạ bị cấm.

    KHÔNG có `kind` (gửi là 422 do `extra=forbid`): đổi loại = xóa + thêm. Loại 1 chỉ nhận `department_id`, loại 2 chỉ
    nhận `company_id` — gửi ô của loại kia thì service trả 400 (cần biết loại của dòng nên không kiểm ở đây).
    """

    model_config = {"extra": "forbid"}

    company_id: int | None = Field(None, gt=0)
    department_id: int | None = Field(None, gt=0)
    position_id: int | None = Field(None, ge=0)
    from_date: ConcurrentDate | None = None
    to_date: ConcurrentDate | None = None
    decision_no: Str50 | None = None
    decision_date: ConcurrentDate | None = None
    note: Str500 | None = None
    counts_scope: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def _check_no_explicit_null(cls, data):
        if isinstance(data, dict):
            bad = [k for k, v in data.items() if v is None and k not in _NULL_ALLOWED]
            if bad:
                raise ValueError(
                    f"Không gửi null cho ô: {', '.join(bad)} — bỏ hẳn khóa đó khỏi payload nếu "
                    "không muốn đổi. Chỉ to_date/decision_date được null tường minh.")
        return data

    @model_validator(mode="after")
    def _check_date_order(self):
        #  Chỉ so khi lượt PATCH gửi đủ cả hai; chốt đủ ở service khi ghép với giá trị cũ.
        if self.from_date is not None and self.to_date is not None and self.to_date < self.from_date:
            raise ValueError(ORDER_ERROR)
        return self


class ConcurrentOut(BaseModel):
    """Hình dạng TRẢ RA một dòng. `status` là SỐ (`ConcurrentStatus`) kèm `status_label`."""

    id: int
    employee_id: int
    #  `kind` số (`ConcurrentKind`) kèm `kind_label`. Loại 2: `department_id` 0, `department_name` "".
    kind: int
    kind_label: str
    company_id: int
    company_name: str = ""
    department_id: int
    department_name: str = ""
    position_id: int = 0
    position_label: str = ""
    from_date: date | None = None
    to_date: date | None = None
    decision_no: str = ""
    decision_date: date | None = None
    note: str = ""
    counts_scope: bool = True
    work_history_id: int = 0
    status: int
    status_label: str
    file_count: int = 0
