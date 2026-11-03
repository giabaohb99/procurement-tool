"""Schema của Chính sách nghỉ phép + Phân bổ chính sách (duoc-CR-717).

Mọi cột `String(n)` khai `max_length` đúng bằng độ dài cột (luật backend-input-limits): chuỗi dài là 422, không
phải 500. Ngày giới hạn năm 2000–2100; danh sách có trần số dòng.
"""
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Code30 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Name150 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Note500 = Annotated[str, StringConstraints(max_length=500)]

MAX_LINES = 50
MAX_BULK = 500


def _check_year(value: date | None) -> date | None:
    if value is not None and not 2000 <= value.year <= 2100:
        raise ValueError("Ngày phải nằm trong khoảng năm 2000–2100")
    return value


# ── Gói chính sách ──────────────────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    code: Code30
    name: Name150
    note: Note500 = ""
    is_active: bool = True


def _reject_null(value):
    """Cột NOT NULL: gửi `null` tường minh là 422 (bỏ trống trường = không đổi), không để vỡ ở MySQL."""
    if value is None:
        raise ValueError("Không được để null — bỏ trường này nếu không muốn đổi")
    return value


class PolicyUpdate(BaseModel):
    """Không có `code` — mã không đổi sau khi tạo."""

    name: Name150 | None = None
    note: Note500 | None = None
    is_active: bool | None = None

    @field_validator("name", "note", "is_active", mode="before")
    @classmethod
    def _not_null(cls, v):
        return _reject_null(v)


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = 0
    code: str = ""
    name: str = ""
    note: str = ""
    is_active: bool = True


class PolicyLineItem(BaseModel):
    leave_type_id: int = Field(..., ge=1)
    annual_days: float = Field(..., ge=0, le=366)

    @field_validator("annual_days")
    @classmethod
    def _half_day_step(cls, v: float) -> float:
        if abs(v * 2 - round(v * 2)) > 1e-9:
            raise ValueError("Số ngày/năm tính theo bước 0.5")
        return v


class PolicyLinesReplace(BaseModel):
    """THAY cả danh sách dòng — trần 50 dòng."""

    items: list[PolicyLineItem] = Field(default_factory=list, max_length=MAX_LINES)


class PolicyLineResponse(PolicyLineItem):
    model_config = ConfigDict(from_attributes=True)

    id: int = 0


# ── Phân bổ ─────────────────────────────────────────────────────────────────────

class AssignmentBase(BaseModel):
    policy_id: int = Field(..., ge=1)
    effective_from: date
    effective_to: date | None = None
    #  D3: ô "Tính lại hạn mức năm nay" mặc định BẬT.
    recalc_current_year: bool = True
    #  D6: ô "Kết thúc chính sách cũ".
    close_previous: bool = False

    @field_validator("effective_from", "effective_to")
    @classmethod
    def _years(cls, v: date | None) -> date | None:
        return _check_year(v)

    @model_validator(mode="after")
    def _range(self):
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("\"Đến ngày\" không được trước \"Từ ngày\"")
        return self


class AssignmentCreate(AssignmentBase):
    employee_id: int = Field(..., ge=1)
    note: Note500 = ""


class AssignmentUpdate(BaseModel):
    """Chỉ sửa `effective_to` (null = không thời hạn), `note`; đổi gói / ngày bắt đầu = xóa rồi tạo lại."""

    effective_to: date | None = None
    note: Note500 | None = None
    recalc_current_year: bool = True

    @field_validator("effective_to")
    @classmethod
    def _years(cls, v: date | None) -> date | None:
        return _check_year(v)

    @field_validator("note", "recalc_current_year", mode="before")
    @classmethod
    def _not_null(cls, v):
        return _reject_null(v)


class AssignmentBulk(AssignmentBase):
    employee_ids: list[int] = Field(..., min_length=1, max_length=MAX_BULK)


class AssignmentPreview(BaseModel):
    policy_id: int = Field(..., ge=1)
    effective_from: date
    effective_to: date | None = None
    close_previous: bool = False
    employee_ids: list[int] | None = Field(None, max_length=MAX_BULK)
    company_id: int | None = Field(None, ge=1)
    department_id: int | None = Field(None, ge=1)
    employment_type: int | None = Field(None, ge=1, le=99)
    job_level: int | None = Field(None, ge=1, le=99)
    #  Chỉ áp khi chọn theo bộ lọc (không truyền `employee_ids`): bỏ người đang có phân bổ hiệu lực hôm nay.
    only_without_active: bool = True

    @field_validator("effective_from", "effective_to")
    @classmethod
    def _years(cls, v: date | None) -> date | None:
        return _check_year(v)

    @model_validator(mode="after")
    def _range(self):
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("\"Đến ngày\" không được trước \"Từ ngày\"")
        return self
