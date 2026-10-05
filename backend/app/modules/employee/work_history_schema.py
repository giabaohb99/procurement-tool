"""Lược đồ vào/ra cho QUÁ TRÌNH CÔNG TÁC (phase 02 của plan
`261003-0837-qua-trinh-lam-viec-nhan-su`). Hợp đồng API khoá cứng ở
`phase-02-backend-api-ap-ho-so-dinh-kem.md` — agent frontend code theo đây,
đổi tên trường/kiểu phải ghi lại ở report.

`extra="forbid"` ở CẢ HAI schema vào: cửa này không có tầng tự phục vụ nào cần
khoá lạ đi lọt như `SelfContactUpdate`, nhưng cấm vẫn rẻ hơn để lọt — gửi
`status` (khoá của hồ sơ, không phải của dòng lịch sử) phải ăn 422 ngay.
"""
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.hr_work_history_codes import WorkEventType

from .field_limits import ProfileDate, Str50, Str500


def _check_event_type_value(v: int) -> int:
    """`event_type` phải là một thành viên THẬT của `WorkEventType` — `0`, số bị
    bỏ trống (`7`) hay số không ai cấp (`99`) đều là lỗi 422, không phải lỗi 400
    của tầng service."""
    try:
        WorkEventType(int(v))
    except ValueError:
        allowed = ", ".join(str(int(x)) for x in WorkEventType)
        raise ValueError(f"Loại sự kiện không hợp lệ — chỉ nhận: {allowed}")
    return int(v)


class WorkHistoryIn(BaseModel):
    """Một dòng quá trình công tác, HR gõ tay. `from_date` = NGÀY HIỆU LỰC (Q1
    chốt gộp 03/10/2026, KHÔNG có `effective_date` riêng)."""

    model_config = {"extra": "forbid"}

    event_type: int
    from_date: ProfileDate
    to_date: ProfileDate | None = None
    company_id: int = Field(0, ge=0)
    department_id: int = Field(0, ge=0)
    position_id: int = Field(0, ge=0)
    decision_no: Str50 = ""
    decision_date: ProfileDate | None = None
    note: Str500 = ""
    #  Hai cờ HÀNH ĐỘNG của riêng lượt gửi này — không phải cột lưu trong bảng.
    close_open_main: bool = False
    apply_to_profile: bool = False

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: int) -> int:
        return _check_event_type_value(v)

    @model_validator(mode="after")
    def _check_date_order(self):
        if self.to_date is not None and self.to_date < self.from_date:
            raise ValueError("Đến ngày phải sau hoặc bằng từ ngày")
        return self


#  M1 (review 03/10/2026) — CHỈ hai ô này được gửi `null` TƯỜNG MINH (Q1: null
#  = xoá/mở lại). Mọi ô khác gửi `null` từng lọt xuống tầng service rồi vỡ ở
#  dưới (`WorkEventType(None)`, so sánh ngày với `None`, cột NOT NULL khi
#  flush) → 500 — chặn ngay ở đây, trả 422 kèm câu rõ ô nào sai.
_UPDATE_NULL_ALLOWED: frozenset[str] = frozenset({"to_date", "decision_date"})


class WorkHistoryUpdate(BaseModel):
    """Sửa một dòng — mọi ô tuỳ chọn (PATCH một phần), khoá lạ bị cấm."""

    model_config = {"extra": "forbid"}

    event_type: int | None = None
    from_date: ProfileDate | None = None
    #  `None` = KHÔNG GỬI (giữ nguyên) ở tầng service (đọc qua `exclude_unset`).
    #  Gửi `null` tường minh để XOÁ `to_date` (mở lại một dòng đã kết thúc) vẫn
    #  phân biệt được, cùng luật với `EmployeeUpdate.hire_date`.
    to_date: ProfileDate | None = None
    company_id: int | None = Field(None, ge=0)
    department_id: int | None = Field(None, ge=0)
    position_id: int | None = Field(None, ge=0)
    decision_no: Str50 | None = None
    decision_date: ProfileDate | None = None
    note: Str500 | None = None
    close_open_main: bool = False
    apply_to_profile: bool = False

    @model_validator(mode="before")
    @classmethod
    def _check_no_explicit_null(cls, data):
        """M1 — PATCH gửi `{"event_type": null}` (hoặc `company_id`/`position_id`/
        `note`/`decision_no`/… null) trước đây lọt qua đây, chạy xuống
        `work_history_service.update` rồi vỡ (500) chứ không báo rõ ô nào sai.
        Chặn ngay ở tầng schema — 422, trước khi chạm DB."""
        if isinstance(data, dict):
            bad = [k for k, v in data.items() if v is None and k not in _UPDATE_NULL_ALLOWED]
            if bad:
                raise ValueError(
                    f"Không gửi null cho ô: {', '.join(bad)} — bỏ hẳn khoá đó khỏi payload nếu "
                    "không muốn đổi. Chỉ to_date/decision_date được null tường minh (để xoá/mở lại).")
        return data

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: int | None) -> int | None:
        return v if v is None else _check_event_type_value(v)

    @model_validator(mode="after")
    def _check_date_order(self):
        #  Chỉ so khi lượt PATCH này gửi ĐỦ CẢ HAI — cùng lý lẽ với
        #  `check_resign_after_hire`: sửa riêng một ô không có gì để so, và
        #  chốt đủ ở tầng service khi ghép với giá trị cũ (xem `work_history_service.update`).
        if self.from_date is not None and self.to_date is not None and self.to_date < self.from_date:
            raise ValueError("Đến ngày phải sau hoặc bằng từ ngày")
        return self


class WorkHistoryOut(BaseModel):
    """Hình dạng TRẢ RA — khớp đúng cột trong hợp đồng API, không thêm trường.

    Cố ý KHÔNG có `event_type_label`: R2/QĐ-11 — frontend tự dịch bằng
    `labelOf(WORK_EVENT_TYPE, String(event_type))` đọc từ `statuses.ts` sinh ở
    phase 01, tiếng Việt không đi qua API.
    """

    id: int
    employee_id: int
    event_type: int
    from_date: date
    to_date: date | None = None
    company_id: int = 0
    company_name: str = ""
    department_id: int = 0
    department_name: str = ""
    position_id: int = 0
    position_label: str = ""
    decision_no: str = ""
    decision_date: date | None = None
    note: str = ""
    applied_at: datetime | None = None
    file_count: int = 0
    is_current: bool = False
    can_apply: bool = False
