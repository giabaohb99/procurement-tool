"""Khuôn dữ liệu của YÊU CẦU SỬA HỒ SƠ (duoc-CR-676) — cửa mở cho MỌI tài khoản đã gắn hồ sơ.

⚠️ Mỗi nhóm khai `extra="forbid"` và chỉ liệt kê ĐÚNG ô được phép. Gửi `department_id`, `phone`,
`company_id`… ở đây là 422 chứ không lờ đi (cùng lý lẽ `SelfContactUpdate`). Độ dài/kiểu lấy đúng
bí danh của `EmployeeUpdate`; các luật giá trị (mã hôn nhân, trình độ, giới tính…) lấy thẳng từ
`EmployeeUpdate` qua `_run_employee_rules`, không chép lại.
"""
from pydantic import BaseModel, Field, ValidationError, model_validator

from .field_limits import MAX_PEOPLE_ROWS, Str20, Str50, Str100, Str255, Str500
from .schema import DateOnly, EmployeeFamilyIn, EmployeeUpdate

#  Ô được XÓA TRẮNG bằng `null` (cột cho phép NULL). Ô khác gửi `null` là 422.
_NULLABLE_FIELDS = frozenset({"date_of_birth", "id_issue_date", "id_expiry_date"})


def clean_error(exc: ValidationError) -> str:
    """Câu báo lỗi gọn của lỗi Pydantic lồng — không `input_value`, không đường dẫn tài liệu."""
    first = exc.errors()[0]
    msg = str(first.get("msg", "")).removeprefix("Value error, ")
    loc = ".".join(str(x) for x in first.get("loc", ()))
    return f"{loc}: {msg}" if loc else msg


class _GroupBase(BaseModel):
    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _check_group(self):
        sent = self.model_dump(exclude_unset=True)
        for key, value in sent.items():
            if value is None and key not in _NULLABLE_FIELDS:
                raise ValueError(f"Ô \"{key}\" không nhận null — muốn xóa thì gửi chuỗi rỗng")
        #  Chạy lại bộ luật giá trị của hồ sơ (mã hôn nhân, trình độ, giới tính, số con…).
        try:
            EmployeeUpdate.model_validate({k: v for k, v in sent.items() if v is not None})
        except ValidationError as exc:
            raise ValueError(clean_error(exc)) from None
        return self


class PersonalChange(_GroupBase):
    gender: int | None = None
    date_of_birth: DateOnly | None = None
    place_of_birth: Str255 | None = None
    ethnicity: Str50 | None = None
    religion: Str50 | None = None
    marital_status: int | None = None
    children_count: int | None = None
    personal_email: Str255 | None = None
    education_level: int | None = None
    major: Str255 | None = None


class BankChange(_GroupBase):
    bank_account_no: Str50 | None = None
    bank_account_name: Str255 | None = None
    bank_name: Str100 | None = None
    bank_branch: Str255 | None = None


class DocumentsChange(_GroupBase):
    id_number: Str20 | None = None
    id_issue_date: DateOnly | None = None
    id_issue_place: Str255 | None = None
    id_expiry_date: DateOnly | None = None
    tax_code: Str20 | None = None
    social_insurance_no: Str20 | None = None
    health_care_place: Str255 | None = None
    health_care_code: Str20 | None = None


class ChangeRequestIn(BaseModel):
    """Thân gửi yêu cầu. Nhóm nào không gửi = không đụng."""

    model_config = {"extra": "forbid"}

    personal: PersonalChange | None = None
    bank: BankChange | None = None
    documents: DocumentsChange | None = None
    #  THAY THẾ TOÀN BỘ danh sách (cùng luật với `PUT /{id}/families`); trần 30 dòng.
    families: list[EmployeeFamilyIn] | None = Field(default=None, max_length=MAX_PEOPLE_ROWS)
    note: Str500 = ""


class RejectIn(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def _not_blank(self):
        if not self.reason.strip():
            raise ValueError("Phải nêu lý do từ chối")
        return self


GROUP_MODELS = {"personal": PersonalChange, "bank": BankChange, "documents": DocumentsChange}
