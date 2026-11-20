"""Schema vào của `POST /api/packaging-cost/impact` (duoc-CR-784): tối đa 500 mã, giá giả định >= 0, khoảng ngày hợp lệ, và
tham số phân trang / tìm / xếp của BẢNG SẢN PHẨM (làm ở máy chủ — KPI vẫn tính trên toàn bộ tập bị ảnh hưởng)."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.employee.field_limits import Str50
from app.modules.product_price.schema import MAX_YEAR, MIN_YEAR, PriceAmount

MAX_CODES = 500
MAX_PAGE_SIZE = 500


class ImpactRequest(BaseModel):
    codes: list[Str50] = Field(min_length=1, max_length=MAX_CODES)
    assumed_prices: dict[Str50, PriceAmount] = Field(default_factory=dict, max_length=MAX_CODES)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    # Bảng sản phẩm bị ảnh hưởng: phân trang + tìm + xếp tại máy chủ (xuất Excel bỏ qua `page` / `page_size`, vẫn theo `q` + xếp).
    page: int = Field(1, ge=1, le=100000)
    page_size: int = Field(50, ge=1, le=MAX_PAGE_SIZE)
    sort_by: str = Field("hh_code", max_length=30)
    sort_dir: str = Field("asc", pattern="^(asc|desc)$")
    q: str = Field("", max_length=100)

    @field_validator("codes")
    @classmethod
    def _clean_codes(cls, v: list[str]) -> list[str]:
        """Bỏ khoảng trắng + mã rỗng + mã trùng (giữ thứ tự người chọn)."""
        out = list(dict.fromkeys(c.strip() for c in v if c and c.strip()))
        if not out:
            raise ValueError("Chọn ít nhất một mã")
        return out

    @field_validator("assumed_prices")
    @classmethod
    def _clean_assumed(cls, v: dict) -> dict:
        """Bỏ khoảng trắng ở khóa mã (cùng luật với `codes`); khóa rỗng bị loại."""
        return {k.strip(): price for k, price in v.items() if k and k.strip()}

    @field_validator("date_from", "date_to")
    @classmethod
    def _year_range(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and not (MIN_YEAR <= v.year <= MAX_YEAR):
            raise ValueError(f"Ngày phải trong khoảng năm {MIN_YEAR}–{MAX_YEAR}")
        return v

    @model_validator(mode="after")
    def _consistent(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Từ ngày không được sau Đến ngày")
        stray = sorted(set(self.assumed_prices) - set(self.codes))
        if stray:
            raise ValueError(f"Giá giả định cho mã chưa chọn: {', '.join(stray[:10])}")
        return self
