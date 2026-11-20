"""Chi phí bao bì của MỘT mã hàng hóa — hàm THUẦN (không DB), chép đúng `productRow()` của bản mẫu (duoc-CR-784).

CP bao bì / chai = chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng; CP / thùng = CP / chai x quy cách.
Tính bằng `Decimal`, làm tròn 4 số lẻ. Ba mốc giá của mỗi thành phần:
  · `old`     — giá cũ (theo luật cũ / mới của `price_state_service`);
  · `new`     — giá mới theo bảng giá (báo giá hoặc lần mua gần nhất);
  · `applied` — giá đang ÁP: giá giả định nếu mã đó được chọn kèm giá giả định, không thì bằng `new`.
Chênh lệch / xu hướng đo `applied` so với `old` (đúng nghĩa "mô phỏng trước khi nhà cung cấp chốt giá").
"""
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from decimal import Decimal
from typing import Protocol

from app.core.packaging_price_codes import CostTrend, CostWarning, PackagingRole

_Q = Decimal("0.0001")
EPS = Decimal("0.000001")
#  Hai thành phần tính THEO THÙNG: giá chia cho quy cách thùng khi gộp vào chi phí / chai.
PER_CARTON = frozenset({PackagingRole.CARTON_LABEL, PackagingRole.CARTON})
#  Nắp / nhãn không có mã là thiếu dữ liệu; nhãn thùng / thùng không có mã là bình thường (sản phẩm không đóng thùng riêng).
WARN_WHEN_NO_CODE = frozenset({PackagingRole.CAP, PackagingRole.LABEL})


class PriceLike(Protocol):
    """Phần của `PriceState` mà tính chi phí cần — tách ra để bài kiểm dựng giá bằng tay."""
    old: Decimal | None
    new: Decimal | None
    unit: str
    floor: Decimal | None
    ceiling: Decimal | None


@dataclass
class PartCost:
    role: PackagingRole
    code: str
    old: Decimal | None
    new: Decimal | None
    applied: Decimal | None
    selected: bool


@dataclass
class ProductCost:
    parts: list[PartCost]
    carton_qty: int
    cost_old_bottle: Decimal | None = None
    cost_new_bottle: Decimal | None = None
    cost_applied_bottle: Decimal | None = None
    diff_bottle: Decimal | None = None
    pct: Decimal | None = None
    cost_old_carton: Decimal | None = None
    cost_applied_carton: Decimal | None = None
    diff_carton: Decimal | None = None
    trend: CostTrend = CostTrend.NO_PRICE
    warnings: list[tuple[CostWarning, PackagingRole | None]] = field(default_factory=list)


@lru_cache(maxsize=16384)
def fold_text(text: str | None) -> str:
    """Chữ thường, bỏ dấu, bỏ khoảng trắng thừa — để so ĐVT ('Cái' = 'cai') và tìm kiếm tên không phân biệt dấu.

    Có nhớ đệm: hàm thuần, và cảnh báo lệch ĐVT gọi nó 2 lần cho MỖI thành phần của MỖI sản phẩm (hàng chục nghìn lần mỗi
    lượt tính) trong khi chỉ có vài chục ĐVT khác nhau — đo ở 20.000 sản phẩm, bỏ nhớ đệm tốn ~0,6 giây.
    """
    folded = unicodedata.normalize("NFD", (text or "").strip().lower())
    return "".join(c for c in folded if unicodedata.category(c) != "Mn").replace("đ", "d")


def price_warnings(price: PriceLike | None, applied: Decimal | None, purchase_unit: str = "") -> list[CostWarning]:
    """Cảnh báo cấp mã vật tư: ĐVT mua khác danh mục (5) · dưới sàn (6) · vượt trần (7)."""
    out: list[CostWarning] = []
    if price is None:
        return out
    if purchase_unit and price.unit and fold_text(purchase_unit) != fold_text(price.unit):
        out.append(CostWarning.UNIT_MISMATCH)
    if applied is not None:
        if price.floor is not None and applied < price.floor:
            out.append(CostWarning.BELOW_FLOOR)
        if price.ceiling is not None and applied > price.ceiling:
            out.append(CostWarning.ABOVE_CEILING)
    return out


def compute_product_cost(bom, prices: dict[str, PriceLike], overrides: dict[str, Decimal | None] | None = None,
                         purchase_units: dict[str, str] | None = None) -> ProductCost:
    """`bom` cần `bottle_code, cap_code, label_code, carton_label_code, carton_code, carton_qty`.

    `overrides` = `{mã đã chọn: giá giả định hoặc None}` — mã có trong dict là "đã chọn" (`selected=True`), giá giả định
    (khác None) thay `new`. `purchase_units` = `{mã: ĐVT lần mua gần nhất}` cho cảnh báo lệch ĐVT.
    """
    overrides = overrides or {}
    purchase_units = purchase_units or {}
    qty = int(bom.carton_qty or 0)
    columns = ((PackagingRole.BOTTLE, bom.bottle_code), (PackagingRole.CAP, bom.cap_code),
               (PackagingRole.LABEL, bom.label_code), (PackagingRole.CARTON_LABEL, bom.carton_label_code),
               (PackagingRole.CARTON, bom.carton_code))
    parts: list[PartCost] = []
    for role, code in columns:
        code = code or ""
        p = prices.get(code) if code else None
        old, new = (p.old, p.new) if p else (None, None)
        selected = code in overrides if code else False
        assumed = overrides.get(code) if selected else None
        parts.append(PartCost(role, code, old, new, assumed if assumed is not None else new, selected))

    def total_raw(field_name: str) -> Decimal | None:
        """Tổng CHƯA làm tròn — chênh lệch / thùng nhân số thô rồi mới làm tròn (bản mẫu nhân số thô)."""
        bottle = getattr(parts[0], field_name)
        if bottle is None:
            return None            # thiếu giá chai → chi phí rỗng
        s = Decimal(bottle)
        for part in parts[1:]:
            v = getattr(part, field_name) or Decimal(0)
            s += (v / qty if qty else Decimal(0)) if part.role in PER_CARTON else v
        return s

    def q(value: Decimal | None) -> Decimal | None:
        return None if value is None else value.quantize(_Q)

    raw_old, raw_new, raw_applied = total_raw("old"), total_raw("new"), total_raw("applied")
    cost = ProductCost(parts=parts, carton_qty=qty, cost_old_bottle=q(raw_old), cost_new_bottle=q(raw_new),
                       cost_applied_bottle=q(raw_applied))
    raw_diff = raw_applied - raw_old if raw_old is not None and raw_applied is not None else None
    if raw_diff is not None:
        cost.diff_bottle = raw_diff.quantize(_Q)
        cost.pct = (raw_diff / raw_old).quantize(Decimal("0.000001")) if raw_old else None
        cost.trend = CostTrend.UP if raw_diff > EPS else CostTrend.DOWN if raw_diff < -EPS else CostTrend.SAME
    if qty:
        cost.cost_old_carton = q(raw_old * qty) if raw_old is not None else None
        cost.cost_applied_carton = q(raw_applied * qty) if raw_applied is not None else None
        cost.diff_carton = q(raw_diff * qty) if raw_diff is not None else None
    cost.warnings = _product_warnings(parts, qty, prices, purchase_units)
    return cost


def _product_warnings(parts, qty, prices, purchase_units):
    out: list[tuple[CostWarning, PackagingRole | None]] = []
    bottle = parts[0]
    if bottle.old is None:
        out.append((CostWarning.MISSING_BOTTLE_PRICE, PackagingRole.BOTTLE))
    for part in parts[1:]:
        if not part.code:
            if part.role in WARN_WHEN_NO_CODE:
                out.append((CostWarning.MISSING_COMPONENT_CODE, part.role))
        elif part.old is None:
            out.append((CostWarning.MISSING_COMPONENT_PRICE, part.role))
    if not qty and any(p.role in PER_CARTON and p.code for p in parts):
        out.append((CostWarning.MISSING_CARTON_QTY, None))
    for part in parts:
        if part.code:
            out += [(w, part.role) for w in price_warnings(prices.get(part.code), part.applied, purchase_units.get(part.code, ""))]
    return out
