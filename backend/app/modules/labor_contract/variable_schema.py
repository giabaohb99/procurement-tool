"""Schema API Danh sách biến mẫu HĐLĐ (duoc-CR-630). `max_length` khớp ĐÚNG `String(n)` ở `variable_model.py`
(SQLite không ép VARCHAR nên chỉ schema giữ được trần — luật backend-input-limits)."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from . import variable_rules as rules
from .variable_model import CODE_LEN, DEFAULT_LEN, DESCRIPTION_LEN, EXAMPLE_LEN, LABEL_LEN

Code = Annotated[str, StringConstraints(strip_whitespace=True, max_length=CODE_LEN)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=LABEL_LEN)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=DESCRIPTION_LEN)]
Example = Annotated[str, StringConstraints(strip_whitespace=True, max_length=EXAMPLE_LEN)]
#  Không `strip`: giá trị mặc định nhiều dòng giữ xuống dòng; `normalize_value` tự dọn theo kiểu.
DefaultRaw = Annotated[str, StringConstraints(max_length=DEFAULT_LEN)]
SortOrder = Annotated[int, Field(ge=0, le=9999)]


def check_value_type(v: int) -> int:
    if v not in rules.VALID_TYPES:
        raise ValueError("Kiểu giá trị không hợp lệ — chỉ nhận: " + ", ".join(str(t) for t in sorted(rules.VALID_TYPES)))
    return v


class VariableCreate(BaseModel):
    """POST — luôn tạo biến TÙY CHỈNH. Mã không tự hạ chữ: sai là 422 rõ ràng."""

    model_config = {"extra": "forbid"}

    code: Code
    label: Label
    description: Description = ""
    example: Example = ""
    value_type: int = 1
    default_value: DefaultRaw = ""
    is_required: bool = False
    is_active: bool = True
    sort_order: SortOrder = 0

    @field_validator("code")
    @classmethod
    def _check_code(cls, v: str) -> str:
        return rules.check_code(v)

    @field_validator("value_type")
    @classmethod
    def _check_type(cls, v: int) -> int:
        return check_value_type(v)

    @model_validator(mode="after")
    def _normalize_default(self):
        self.default_value = rules.normalize_value(self.value_type, self.default_value)
        return self


class VariableUpdate(BaseModel):
    """PATCH (`exclude_unset`). Luật theo loại biến (hệ thống chỉ nhãn/mô tả/ẩn…) kiểm ở service;
    chuẩn hóa `default_value` cũng ở service vì cần kiểu GỘP với giá trị cũ."""

    model_config = {"extra": "forbid"}

    code: Code | None = None
    label: Label | None = None
    description: Description | None = None
    example: Example | None = None
    value_type: int | None = None
    default_value: DefaultRaw | None = None
    is_required: bool | None = None
    is_active: bool | None = None
    is_hidden: bool | None = None
    sort_order: SortOrder | None = None

    @field_validator("value_type")
    @classmethod
    def _check_type(cls, v):
        return None if v is None else check_value_type(v)


class VariableOut(BaseModel):
    id: int
    code: str
    source: int
    value_type: int
    label: str
    description: str = ""
    example: str = ""
    default_value: str = ""
    is_required: bool = False
    is_active: bool = True
    is_hidden: bool = False
    sort_order: int = 0
    template_count: int = 0
    group: str = ""
    created_at: datetime | None = None
    created_by_name: str = ""
