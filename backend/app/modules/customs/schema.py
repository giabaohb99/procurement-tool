"""Schema màn sửa danh mục hóa chất theo văn bản (bao-CR-470, HQ6 P-01).

Mọi cột chữ khai `max_length` khớp ĐÚNG `String(n)` ở `model.py`: thiếu thì chuỗi quá
dài đi thẳng xuống MySQL và ra lỗi 500 thay vì câu "tối đa n ký tự" (duoc-CR-316).
Bộ test chạy SQLite, không ép độ dài — nên chốt phải nằm ở đây.
"""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import RegulationList

_LIST_CODES = {int(x) for x in RegulationList}


def _check_list_code(v):
    if v is not None and int(v) not in _LIST_CODES:
        raise ValueError(f"Danh sách không hợp lệ: {v}")
    return v


class RegulationCreate(BaseModel):
    list_code: int
    name: str = Field(..., min_length=1, max_length=500)
    name_vi: str = Field("", max_length=500)
    cas_no: str = Field("", max_length=40)
    category: str = Field("", max_length=100)
    #  Ngưỡng khối lượng (kg) — chỉ có nghĩa với Phụ lục IV của NĐ 24/2026.
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str = Field("", max_length=255)
    note: str = Field("", max_length=500)
    is_active: bool = True

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationUpdate(BaseModel):
    list_code: int | None = None
    name: str | None = Field(None, min_length=1, max_length=500)
    name_vi: str | None = Field(None, max_length=500)
    cas_no: str | None = Field(None, max_length=40)
    category: str | None = Field(None, max_length=100)
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str | None = Field(None, max_length=255)
    note: str | None = Field(None, max_length=500)
    is_active: bool | None = None

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_code: int
    name: str = ""
    name_vi: str = ""
    cas_no: str = ""
    category: str = ""
    threshold_kg: float | None = None
    banned_year: int | None = None
    legal_basis: str = ""
    note: str = ""
    is_active: bool = True
