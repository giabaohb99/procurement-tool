"""Tổng hợp theo sản phẩm: MỌI mã hàng hóa có định mức bao bì, chi phí bao bì / chai cũ so với mới và xu hướng (duoc-CR-784).

Đúng tab "Tổng hợp" của bản mẫu. Dùng lại nguyên `compute_product_cost` và `get_price_states` của màn Tác động giá, nên cùng
công thức và cùng luật giá cũ / mới (báo giá tính là giá mới, dòng giá 0 bị bỏ qua) — chỉ khác là KHÔNG có mã được chọn,
không có giá giả định: `applied` luôn bằng `new`.

NĂM truy vấn cố định bất kể số dòng định mức: (1) toàn bộ định mức (đầu phiếu nối bảng thành phần, chỉ các cột cần), (2–5) bốn truy vấn của `get_price_states`
cho mọi mã thành phần (không tính số gộp min / max vì màn này không hiện). Chi phí tính hết trong bộ nhớ; lọc `q` + lọc nâng cao, đếm theo xu
hướng, lọc xu hướng, xếp và cắt trang đều SAU khi tính xong, nên số truy vấn không đổi theo trang / bộ lọc.
"""
from dataclasses import replace

from sqlalchemy.orm import Session

from app.modules.product_price.price_state_service import get_price_states

from .bom_parts_service import load_bom_rows
from .cost_service import compute_product_cost
from .impact_filters import TREND_FILTERS, ImpactFilters
from .impact_service import PART_SORT_GETTERS, SORT_GETTERS, arrange_products, bom_codes, product_row

#  Khóa cột được phép xếp (whitelist); khóa lạ → xếp theo mã hàng hóa. `cost_new_bottle` = giá mới (không giả định).
OVERVIEW_SORT_GETTERS = {
    **{k: SORT_GETTERS[k] for k in ("hh_code", "hh_name", "carton_qty", "cost_old_bottle", "diff_bottle", "diff_carton", "pct")},
    "cost_new_bottle": lambda bom, cost: cost.cost_new_bottle,
    **PART_SORT_GETTERS,       # năm cột thành phần xếp theo giá mới của thành phần (không giả định nên bằng giá đang áp)
}


def build_product_overview(db: Session, *, q: str = "", trend: str = "all", sort_by: str = "hh_code", sort_dir: str = "asc",
                           filters: ImpactFilters | None = None, page: int | None = None, page_size: int = 50,
                           scope_cond=None) -> dict:
    """`{items, total, counts}`. `counts` = `{all, up, down, flat, missing}` trên tập đã lọc `q` + lọc nâng cao `filters`
    NHƯNG chưa lọc `trend` (để chip xu hướng luôn hiện đủ số và phản ánh đúng tập đang xem); `total` = số dòng sau mọi bộ
    lọc; `page=None` = lấy đủ (xuất Excel). `filters.trend` bị bỏ qua — xu hướng đi bằng tham số `trend` riêng (chip)."""
    bom_rows = load_bom_rows(db)
    counts = {"all": 0, "up": 0, "down": 0, "flat": 0, "missing": 0}
    if not bom_rows:
        return {"items": [], "total": 0, "counts": counts}
    needed = set().union(*(bom_codes(b) for b in bom_rows))
    states = get_price_states(db, needed, scope_cond=scope_cond, also=needed, stats_codes=set())   # chỉ cần cũ / mới + ngưỡng
    units = {c: s.p1.unit for c, s in states.items() if s.p1}
    names = {c: s.name for c, s in states.items()}

    items = [(bom, compute_product_cost(bom, states, None, units)) for bom in bom_rows]
    arranged = arrange_products(items, q=q, sort_by=sort_by, sort_dir=sort_dir, getters=OVERVIEW_SORT_GETTERS,
                               filters=replace(filters, trend="all") if filters else None)
    counts["all"] = len(arranged)
    for key, code in TREND_FILTERS.items():
        counts[key] = sum(1 for _, cost in arranged if cost.trend == code)
    if trend in TREND_FILTERS:
        arranged = [it for it in arranged if it[1].trend == TREND_FILTERS[trend]]
    window = arranged if page is None else arranged[(page - 1) * page_size:page * page_size]
    return {"items": [product_row(bom, cost, names) for bom, cost in window], "total": len(arranged), "counts": counts}
