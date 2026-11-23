"""Tác động giá bao bì: chọn các mã chai / nắp / nhãn / nhãn thùng / thùng (kèm giá giả định) → sản phẩm bị ảnh hưởng
(duoc-CR-784, phase 04). Đúng `renderImpact()` của bản mẫu.

SÁU truy vấn cố định bất kể số mã đã chọn / số dòng định mức: (1) định mức có dùng ít nhất một mã đã chọn (chỉ các cột cần,
không cột kiểm toán), (2–6) năm truy vấn của `get_price_states` cho mọi mã thành phần (sổ giá hai tầng: mã đã chọn có đủ
min / max, mã thành phần khác chỉ lấy cũ / mới). "Số sản phẩm dùng" mỗi mã đã chọn đếm
ngay từ (1) — không cần truy vấn riêng. Phân trang / tìm / xếp bảng sản phẩm làm ở máy chủ SAU khi tính xong chi phí (KPI cần
toàn bộ tập bị ảnh hưởng), nên số truy vấn không đổi theo trang.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.packaging_price_codes import CostTrend, CostWarning
from app.modules.product_price.price_state_service import PriceState, get_price_states

from .cost_service import ProductCost, compute_product_cost, fold_text, price_warnings
from .impact_filters import ImpactFilters, filter_products
from .model import PackagingBom
from .numbers import iso, num
from .sorting import sort_blank_last

PART_COLUMNS = ("bottle_code", "cap_code", "label_code", "carton_label_code", "carton_code")
OTHER_GROUP = "Khác"


def bom_codes(bom: PackagingBom) -> set[str]:
    return {c for c in (getattr(bom, col) for col in PART_COLUMNS) if c}


def product_row(bom: PackagingBom, cost: ProductCost, names: dict[str, str]) -> dict:
    """Một dòng `products[]` của hợp đồng API — số kèm mã, KHÔNG gửi câu tiếng Việt."""
    return {
        "hh_code": bom.hh_code, "hh_name": bom.hh_name, "legal_name": bom.legal_name, "carton_qty": cost.carton_qty,
        "parts": [{"role": int(p.role), "code": p.code, "name": names.get(p.code, ""), "old": num(p.old),
                   "new": num(p.new), "applied": num(p.applied), "selected": p.selected} for p in cost.parts],
        "cost_old_bottle": num(cost.cost_old_bottle), "cost_new_bottle": num(cost.cost_new_bottle),
        "cost_applied_bottle": num(cost.cost_applied_bottle), "diff_bottle": num(cost.diff_bottle),
        "pct": num(cost.pct, 6), "cost_old_carton": num(cost.cost_old_carton),
        "cost_applied_carton": num(cost.cost_applied_carton), "diff_carton": num(cost.diff_carton),
        "trend": int(cost.trend),
        "warnings": [{"kind": int(k), **({"role": int(r)} if r is not None else {})} for k, r in cost.warnings],
    }


def selected_row(code: str, st: PriceState, assumed: Decimal | None, usage: int) -> dict:
    applied = assumed if assumed is not None else st.new
    diff = (applied - st.old) if applied is not None and st.old is not None else None
    warnings = [int(w) for w in price_warnings(st, applied, st.p1.unit if st.p1 else "")]
    if applied is None:
        warnings.append(int(CostWarning.MISSING_COMPONENT_PRICE))   # mã đã chọn mà chưa có giá nào
    return {"code": code, "name": st.name, "group": st.group or OTHER_GROUP, "unit": st.unit, "old": num(st.old),
            "new": num(st.new), "assumed": num(assumed), "applied": num(applied), "diff": num(diff),
            "pct": num(diff / st.old, 6) if diff is not None and st.old else None, "usage": usage,
            "min": num(st.min), "max": num(st.max), "floor": num(st.floor), "ceiling": num(st.ceiling),
            "last_date": iso(st.last_date), "warnings": warnings}


def part_price_getter(role: int):
    """Khóa xếp của cột thành phần `role` (1..5): giá ĐANG ÁP của thành phần đó — con số kéo chi phí (giá mới, hoặc giá giả
    định nếu mã được chọn kèm giá). Sản phẩm không có mã ở vai trò đó, hoặc mã chưa có giá → trống → xuống cuối cả hai chiều."""
    def getter(bom, cost):
        part = cost.parts[role - 1]
        return part.applied if part.code else None
    return getter


def part_tie_getter(role: int):
    """Khóa phụ khi xếp theo cột thành phần: mã thành phần rồi mã hàng hóa (cùng giá thì gom các sản phẩm dùng chung một mã)."""
    return lambda bom, cost: (cost.parts[role - 1].code, bom.hh_code)


#  Khóa xếp cột thành phần → vai trò (`PackagingRole`). Đặt tên theo tên cột định mức, không theo số, cho URL dễ đọc.
PART_SORT_ROLES = {"part_bottle": 1, "part_cap": 2, "part_label": 3, "part_carton_label": 4, "part_carton": 5}
PART_SORT_GETTERS = {key: part_price_getter(role) for key, role in PART_SORT_ROLES.items()}
#  Khóa phụ riêng của từng khóa xếp; khóa nào không khai thì hòa theo mã hàng hóa tăng dần.
SORT_TIES = {key: part_tie_getter(role) for key, role in PART_SORT_ROLES.items()}

#  Khóa cột của bảng sản phẩm được phép xếp (whitelist); khóa lạ → xếp theo mã hàng hóa. Số lấy từ `ProductCost` (đúng con số hiện).
SORT_GETTERS = {
    "hh_code": lambda bom, cost: fold_text(bom.hh_code), "hh_name": lambda bom, cost: fold_text(bom.hh_name),
    "carton_qty": lambda bom, cost: cost.carton_qty or None,
    "cost_old_bottle": lambda bom, cost: cost.cost_old_bottle, "cost_applied_bottle": lambda bom, cost: cost.cost_applied_bottle,
    "diff_bottle": lambda bom, cost: cost.diff_bottle, "diff_carton": lambda bom, cost: cost.diff_carton,
    "cost_old_carton": lambda bom, cost: cost.cost_old_carton, "cost_applied_carton": lambda bom, cost: cost.cost_applied_carton,
    "pct": lambda bom, cost: cost.pct, "trend": lambda bom, cost: int(cost.trend),
    **PART_SORT_GETTERS,
}
IMPACT_BOM_COLUMNS = (PackagingBom.hh_code, PackagingBom.hh_name, PackagingBom.legal_name, *(getattr(PackagingBom, c) for c in PART_COLUMNS),
                      PackagingBom.carton_qty)


def _matches(bom, terms: list[str]) -> bool:
    """Mọi từ khóa (đã bỏ dấu) đều nằm trong mã HH + tên + tên pháp lý + mã thành phần — đúng ô tìm của bảng."""
    haystack = fold_text(" ".join([bom.hh_code, bom.hh_name, bom.legal_name or "", *bom_codes(bom)]))
    return all(term in haystack for term in terms)


def arrange_products(items: list[tuple], *, q: str = "", sort_by: str = "hh_code", sort_dir: str = "asc",
                     getters: dict = SORT_GETTERS, filters: ImpactFilters | None = None) -> list[tuple]:
    """Lọc theo `q` (+ `filters` nâng cao) rồi xếp `(bom, cost)`: ô trống xuống CUỐI cả hai chiều, khóa phụ là mã hàng hóa
    tăng dần (luật §8; cột thành phần: mã thành phần rồi mã hàng hóa, xem `SORT_TIES`).

    `getters` = bảng khóa cột được phép xếp của màn gọi (mặc định: của Tác động giá); khóa lạ → xếp theo mã hàng hóa.
    """
    terms = fold_text(q).split()
    if terms:
        items = [it for it in items if _matches(it[0], terms)]
    items = filter_products(items, filters)
    known = sort_by in getters
    getter = getters[sort_by if known else "hh_code"]
    tie = SORT_TIES.get(sort_by) if known else None
    return sort_blank_last(items, lambda it: getter(*it), (lambda it: tie(*it)) if tie else (lambda it: it[0].hh_code),
                           desc=sort_dir == "desc")


def compute_impact(db: Session, codes: list[str], assumed: dict[str, Decimal], *, date_from: date | None = None,
                   date_to: date | None = None, scope_cond=None, page: int | None = None, page_size: int = 50,
                   q: str = "", sort_by: str = "hh_code", sort_dir: str = "asc", filters: ImpactFilters | None = None) -> dict:
    """`{selected, kpis, products, products_total}`. Mã không có trong định mức nào vẫn trả 200 với `products` rỗng.

    Chi phí của MỌI sản phẩm bị ảnh hưởng tính trong bộ nhớ (cần cho KPI toàn bộ), còn `products` chỉ dựng dòng cho trang
    được hỏi: `page=None` = tất cả (xuất Excel), ngược lại cắt `page` / `page_size` SAU khi lọc `q` + `filters` (lọc nâng cao) và
    xếp `sort_by` / `sort_dir`. `products_total` = số sản phẩm sau các bộ lọc; `kpis.affected_products` = số sản phẩm bị ảnh
    hưởng (chưa lọc gì) — hiệu hai số là "Đang lọc x / M" của giao diện.
    """
    chosen = set(codes)
    bom_rows = db.execute(select(*IMPACT_BOM_COLUMNS).where(or_(*[getattr(PackagingBom, c).in_(chosen) for c in PART_COLUMNS]))
                          .order_by(PackagingBom.hh_code)).all()
    needed = chosen.union(*(bom_codes(b) for b in bom_rows)) if bom_rows else set(chosen)
    states = get_price_states(db, needed, date_from=date_from, date_to=date_to, scope_cond=scope_cond, also=needed,
                              stats_codes=chosen)   # min / max chỉ hiện ở các mã ĐÃ CHỌN; mã thành phần khác chỉ cần cũ / mới
    units = {c: s.p1.unit for c, s in states.items() if s.p1}
    names = {c: s.name for c, s in states.items()}
    overrides = {c: assumed.get(c) for c in chosen}

    usage = dict.fromkeys(chosen, 0)
    items: list[tuple] = []
    for bom in bom_rows:
        for c in bom_codes(bom) & chosen:
            usage[c] += 1
        items.append((bom, compute_product_cost(bom, states, overrides, units)))

    selected = [selected_row(c, states[c], assumed.get(c), usage[c]) for c in codes]
    by_group: dict[str, int] = {}
    for row in selected:
        by_group[row["group"]] = by_group.get(row["group"], 0) + 1
    costs = [cost for _, cost in items]
    cartons = [c.diff_carton for c in costs if c.diff_carton is not None]
    bottles = [c.diff_bottle for c in costs if c.diff_bottle is not None]
    kpis = {"selected_count": len(codes), "selected_by_group": by_group,
            "assumed_count": sum(1 for c in codes if assumed.get(c) is not None),
            "affected_products": len(bom_rows),
            "increased": sum(1 for c in costs if c.trend == CostTrend.UP),
            "decreased": sum(1 for c in costs if c.trend == CostTrend.DOWN),
            "max_increase_carton": num(max(cartons)) if cartons else None,
            "max_increase_bottle": num(max(bottles)) if bottles else None}

    arranged = arrange_products(items, q=q, sort_by=sort_by, sort_dir=sort_dir, filters=filters)
    window = arranged if page is None else arranged[(page - 1) * page_size:page * page_size]
    return {"selected": selected, "kpis": kpis, "products": [product_row(bom, cost, names) for bom, cost in window],
            "products_total": len(arranged)}
