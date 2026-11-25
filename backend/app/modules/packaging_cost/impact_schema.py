"""Schema vào của `POST /api/packaging-cost/impact` (duoc-CR-784): tối đa 500 mã, giá giả định >= 0, khoảng ngày hợp lệ, và
tham số phân trang / tìm / lọc nâng cao / xếp của BẢNG SẢN PHẨM (làm ở máy chủ — KPI vẫn tính trên toàn bộ tập bị ảnh hưởng)."""
from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.packaging_price_codes import PackagingRole
from app.modules.employee.field_limits import Str50
from app.modules.product_price.schema import MAX_YEAR, MIN_YEAR, PriceAmount

from .impact_filters import ImpactFilters, check_range, make_range

MAX_CODES = 500
MAX_PAGE_SIZE = 500
#  Trần của các ô khoảng số (đồng / quy cách): rộng hơn mọi giá bao bì thật, chặn giá trị phi lý và vô cực / NaN.
RANGE_LIMIT = 1e12
MAX_CARTON_QTY = 1_000_000
ROLE_VALUES = tuple(int(role) for role in PackagingRole)

#  Ô khoảng số: biên có thể âm (chênh lệch giảm), không nhận NaN / vô cực.
RangeBound = Annotated[Optional[float], Field(ge=-RANGE_LIMIT, le=RANGE_LIMIT, allow_inf_nan=False)]


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
    # Lọc nâng cao của bảng sản phẩm (lọc trong bộ nhớ, sau khi tính chi phí; KPI không đổi; xuất Excel theo cùng bộ lọc).
    trend: Literal["all", "up", "down", "flat", "missing"] = "all"
    part_roles: list[int] = Field(default_factory=list, max_length=len(ROLE_VALUES))
    carton_qty_min: Optional[int] = Field(None, ge=0, le=MAX_CARTON_QTY)
    carton_qty_max: Optional[int] = Field(None, ge=0, le=MAX_CARTON_QTY)
    diff_bottle_min: RangeBound = None
    diff_bottle_max: RangeBound = None
    diff_carton_min: RangeBound = None
    diff_carton_max: RangeBound = None
    cost_new_bottle_min: RangeBound = None
    cost_new_bottle_max: RangeBound = None
    warnings_only: bool = False

    @field_validator("part_roles")
    @classmethod
    def _clean_roles(cls, v: list[int]) -> list[int]:
        """Vai trò hợp lệ là một số của `PackagingRole` (hiện 1..5); bỏ trùng, giữ thứ tự."""
        bad = [r for r in v if r not in ROLE_VALUES]
        if bad:
            raise ValueError(f"Vai trò thành phần không hợp lệ: {bad[:5]}")
        return list(dict.fromkeys(v))

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
        for name in ("carton_qty", "diff_bottle", "diff_carton", "cost_new_bottle"):
            check_range(name, getattr(self, f"{name}_min"), getattr(self, f"{name}_max"))
        stray = sorted(set(self.assumed_prices) - set(self.codes))
        if stray:
            raise ValueError(f"Giá giả định cho mã chưa chọn: {', '.join(stray[:10])}")
        return self

    def to_filters(self) -> ImpactFilters:
        """Gom các trường lọc nâng cao thành `ImpactFilters` cho `compute_impact`."""
        def bounds(name: str):
            return make_range(getattr(self, f"{name}_min"), getattr(self, f"{name}_max"))
        return ImpactFilters(trend=self.trend, part_roles=frozenset(self.part_roles), carton_qty=bounds("carton_qty"),
                             diff_bottle=bounds("diff_bottle"), diff_carton=bounds("diff_carton"),
                             cost_new_bottle=bounds("cost_new_bottle"), warnings_only=self.warnings_only)
