"""Schema ghi / đọc của báo giá + ngưỡng giá (duoc-CR-784). Mọi `String(n)` có `max_length` đúng n (backend-input-limits)."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.employee.field_limits import Str50, Str500

#  Tiền VNĐ chưa VAT: 0..10^12 (cột Numeric(18,4) nhận tới 10^14 — trần này chặn số dán nhầm).
PriceAmount = Annotated[Decimal, Field(ge=0, le=Decimal("1000000000000"), decimal_places=4)]
VatPercent = Annotated[Decimal, Field(ge=0, lt=100, decimal_places=2)]
#  Ngày hiệu lực báo giá: dải năm hợp lý (MySQL nhận tới 9999, ngày năm 0001 làm lệch "giá mới").
MIN_YEAR, MAX_YEAR = 2000, 2100


def _check_valid_from(v: Optional[date]) -> Optional[date]:
    if v is not None and not (MIN_YEAR <= v.year <= MAX_YEAR):
        raise ValueError(f"Ngày hiệu lực phải trong khoảng năm {MIN_YEAR}–{MAX_YEAR}")
    return v


def _check_code(v: Optional[str]) -> Optional[str]:
    if v is not None:
        v = v.strip()
        if not v:
            raise ValueError("Mã sản phẩm không được để trống")
    return v


class QuoteCreate(BaseModel):
    product_code: Str50
    supplier_code: Str50 = ""
    price: PriceAmount
    vat: VatPercent = Decimal(0)
    valid_from: date
    note: Str500 = ""

    _code = field_validator("product_code")(_check_code)
    _from = field_validator("valid_from")(_check_valid_from)


class QuoteUpdate(BaseModel):
    product_code: Optional[Str50] = None
    supplier_code: Optional[Str50] = None
    price: Optional[PriceAmount] = None
    vat: Optional[VatPercent] = None
    valid_from: Optional[date] = None
    note: Optional[Str500] = None

    _code = field_validator("product_code")(_check_code)
    _from = field_validator("valid_from")(_check_valid_from)


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_code: str
    supplier_code: str
    price: Decimal
    vat: Decimal
    valid_from: date
    note: str


def _check_floor_ceiling(floor, ceiling) -> None:
    if floor is not None and ceiling is not None and floor > ceiling:
        raise ValueError("Ngưỡng sàn không được lớn hơn ngưỡng trần")


class LimitCreate(BaseModel):
    product_code: Str50
    floor_price: Optional[PriceAmount] = None
    ceiling_price: Optional[PriceAmount] = None
    note: Str500 = ""

    _code = field_validator("product_code")(_check_code)

    @model_validator(mode="after")
    def _floor_le_ceiling(self):
        _check_floor_ceiling(self.floor_price, self.ceiling_price)
        return self


class LimitUpdate(BaseModel):
    product_code: Optional[Str50] = None
    floor_price: Optional[PriceAmount] = None
    ceiling_price: Optional[PriceAmount] = None
    note: Optional[Str500] = None

    _code = field_validator("product_code")(_check_code)

    @model_validator(mode="after")
    def _floor_le_ceiling(self):
        _check_floor_ceiling(self.floor_price, self.ceiling_price)
        return self


class LimitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_code: str
    floor_price: Optional[Decimal] = None
    ceiling_price: Optional[Decimal] = None
    note: str
