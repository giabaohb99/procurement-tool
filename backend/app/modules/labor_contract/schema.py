"""Schema HĐLĐ. `max_length` khớp ĐÚNG `String(n)` ở `model.py`; tiền là số nguyên 0..10^12."""
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.modules.employee.field_limits import ProfileDate

from . import rules
from .template_schema import check_contract_type

Str50 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
Str100 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Str255 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
Str500 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
#  Đồng NGUYÊN, không lẻ; trần 10^12 để không tràn BigInteger khi cộng lương + phụ cấp.
Money = Annotated[int, Field(ge=0, le=10**12)]


class LaborContractCreate(BaseModel):
    """`job_title` / `work_location` để `None` thì lấy từ hồ sơ nhân sự (chức vụ / nơi làm việc)."""

    model_config = {"extra": "forbid"}

    contract_type: int
    contract_no: Str50 = ""
    start_date: ProfileDate
    end_date: ProfileDate | None = None
    job_title: Str100 | None = None
    work_location: Str255 | None = None
    base_salary: Money = 0
    insurance_salary: Money = 0
    allowance: Money = 0
    allowance_note: Str500 = ""
    note: Str500 = ""

    @field_validator("contract_type")
    @classmethod
    def _check_type(cls, v: int) -> int:
        return check_contract_type(v)

    @model_validator(mode="after")
    def _check_dates(self):
        rules.check_dates(self.contract_type, self.start_date, self.end_date)
        return self


class LaborContractUpdate(BaseModel):
    """PATCH (chỉ khi DRAFT). Ràng buộc ngày kiểm lại trên giá trị GỘP ở service."""

    model_config = {"extra": "forbid"}

    contract_type: int | None = None
    contract_no: Str50 | None = None
    start_date: ProfileDate | None = None
    end_date: ProfileDate | None = None
    job_title: Str100 | None = None
    work_location: Str255 | None = None
    base_salary: Money | None = None
    insurance_salary: Money | None = None
    allowance: Money | None = None
    allowance_note: Str500 | None = None
    note: Str500 | None = None

    @field_validator("contract_type")
    @classmethod
    def _check_type(cls, v):
        return None if v is None else check_contract_type(v)


class GenerateIn(BaseModel):
    model_config = {"extra": "forbid"}
    template_id: int = Field(ge=1)


class TransitionIn(BaseModel):
    """`date` = ngày ký (→ SIGNED) hoặc ngày chấm dứt (→ TERMINATED)."""

    model_config = {"extra": "forbid"}

    to_status: int
    date: ProfileDate | None = None
    reason: Str500 = ""


class LaborContractOut(BaseModel):
    """Hình dạng TRẢ RA. Không `url` / `file_key` / id tệp — chỉ cờ `has_*_file`."""

    id: int
    code: str
    contract_no: str = ""
    employee_id: int
    company_id: int
    company_name: str = ""
    department_id: int = 0
    department_name: str = ""
    template_id: int = 0
    template_name: str = ""
    contract_type: int
    status: int
    effective_status: int
    sign_date: date | None = None
    start_date: date
    end_date: date | None = None
    job_title: str = ""
    work_location: str = ""
    base_salary: int = 0
    insurance_salary: int = 0
    allowance: int = 0
    allowance_note: str = ""
    note: str = ""
    has_generated_file: bool = False
    generated_at: datetime | None = None
    has_signed_file: bool = False
    terminated_date: date | None = None
    terminate_reason: str = ""
    created_at: datetime | None = None
    created_by_name: str = ""
    can_edit: bool = False
    can_delete: bool = False
    can_generate: bool = False
    can_print: bool = False
    can_upload_signed: bool = False
    transitions: list[int] = []
