"""Lọc nâng cao của bảng SẢN PHẨM BỊ ẢNH HƯỞNG (duoc-CR-784) — hàm thuần trên cặp `(bom, cost)` đã tính xong.

Lọc làm trong bộ nhớ SAU khi tính chi phí (cùng chỗ với lọc `q`): KPI và bảng mã đã chọn vẫn tính trên toàn bộ tập bị ảnh
hưởng, số truy vấn không đổi theo bộ lọc. Mọi điều kiện ghép bằng VÀ; trong riêng `part_roles` là HOẶC. Khoảng số có biên
đóng (`>= min` và `<= max`); sản phẩm có giá trị TRỐNG (chưa tính được) bị loại khi khoảng đó đang bật, vì "không biết" không
thể nằm trong một khoảng.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.packaging_price_codes import CostTrend

#  Mã chữ của URL / thân yêu cầu → mã số xu hướng `CostTrend`; "all" không lọc.
TREND_FILTERS = {"up": CostTrend.UP, "down": CostTrend.DOWN, "flat": CostTrend.SAME, "missing": CostTrend.NO_PRICE}

Range = tuple[Decimal | None, Decimal | None]
_PCT_STEP = Decimal("0.1")   # màn hiện "% chênh" một số lẻ — khoảng lọc so với đúng số đang hiện


def make_range(low: float | int | None, high: float | int | None) -> Range:
    """Cặp biên của yêu cầu (float / int / None) → `Range` Decimal. Đi qua `str` để 0.1 không thành 0.1000000000000000055."""
    return (None if low is None else Decimal(str(low)), None if high is None else Decimal(str(high)))


def check_range(name: str, low: float | int | None, high: float | int | None) -> None:
    """Báo `ValueError` khi biên dưới lớn hơn biên trên (dùng chung cho thân `POST /impact` và tham số `GET /product-overview`)."""
    if low is not None and high is not None and low > high:
        raise ValueError(f"Khoảng lọc không hợp lệ ({name}): giá trị nhỏ nhất lớn hơn giá trị lớn nhất")


@dataclass(frozen=True)
class ImpactFilters:
    """Bộ lọc nâng cao; mặc định = không lọc gì."""

    trend: str = "all"
    #  Vai trò (`PackagingRole`, 1..5): giữ sản phẩm có MÃ ĐÃ CHỌN ở ít nhất một trong các vai trò này.
    part_roles: frozenset[int] = frozenset()
    carton_qty: Range = (None, None)
    diff_bottle: Range = (None, None)
    diff_carton: Range = (None, None)
    cost_new_bottle: Range = (None, None)
    #  Hai khoảng chỉ màn Tổng hợp theo sản phẩm dùng: CP bao bì / chai cũ, và % chênh (ĐƠN VỊ %, so với số một chữ số lẻ đang hiện).
    cost_old_bottle: Range = (None, None)
    pct: Range = (None, None)
    #  True = vai trò xét theo MÃ CÓ MẶT trong định mức (màn không có mã được chọn: Tổng hợp theo sản phẩm); False = xét theo
    #  mã ĐÃ CHỌN (Tác động giá).
    roles_by_presence: bool = False
    #  Chỉ sản phẩm đang có ít nhất một cảnh báo (thiếu giá / mã, thiếu quy cách thùng, lệch ĐVT, dưới sàn, vượt trần).
    warnings_only: bool = False

    @property
    def active(self) -> bool:
        return (self.trend in TREND_FILTERS or bool(self.part_roles) or self.warnings_only
                or any(low is not None or high is not None
                       for low, high in (self.carton_qty, self.diff_bottle, self.diff_carton, self.cost_new_bottle,
                                         self.cost_old_bottle, self.pct)))


def _in_range(value: Decimal | int | None, bounds: Range) -> bool:
    low, high = bounds
    if low is None and high is None:
        return True
    if value is None:
        return False
    return (low is None or value >= low) and (high is None or value <= high)


def keep_product(cost, flt: ImpactFilters) -> bool:
    """Sản phẩm (đã có `cost: ProductCost`) có qua mọi điều kiện của `flt` không."""
    if flt.trend in TREND_FILTERS and cost.trend != TREND_FILTERS[flt.trend]:
        return False
    if flt.part_roles and not any((p.code if flt.roles_by_presence else p.selected) and int(p.role) in flt.part_roles
                                  for p in cost.parts):
        return False
    if flt.warnings_only and not cost.warnings:
        return False
    shown_pct = None if cost.pct is None else (cost.pct * 100).quantize(_PCT_STEP, rounding=ROUND_HALF_UP)
    return (_in_range(cost.carton_qty or None, flt.carton_qty) and _in_range(cost.diff_bottle, flt.diff_bottle)
            and _in_range(cost.diff_carton, flt.diff_carton) and _in_range(cost.cost_applied_bottle, flt.cost_new_bottle)
            and _in_range(cost.cost_old_bottle, flt.cost_old_bottle) and _in_range(shown_pct, flt.pct))


def filter_products(items: list[tuple], flt: ImpactFilters | None) -> list[tuple]:
    """Giữ các cặp `(bom, cost)` qua `flt`; không lọc thì trả nguyên danh sách."""
    if flt is None or not flt.active:
        return items
    return [it for it in items if keep_product(it[1], flt)]
