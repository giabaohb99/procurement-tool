"""Giá mua 5 lần gần nhất của từng mã VTBB — ma trận một dòng một mã (duoc-CR-784, tab của bản mẫu `renderMatrix`).

NĂM truy vấn cố định bất kể số mã, số lần hiển thị `n` hay bộ lọc (luật "API báo cáo phải nhanh nhất"):
  1. cột mã thành phần của định mức; 2. mã có báo giá — hai truy vấn này dựng tập mã VTBB, cùng luật với Bảng giá;
  3. sổ giá `price > 0`: `latest_priced_query.latest_priced_by_code` lấy `n` lần gần nhất (ngày giảm, doc_id giảm, id giảm) kèm
     `COUNT(*)` = số lần có giá — một câu, không hàm cửa sổ;
  4. `tab_product` (tên / nhóm / ĐVT);  5. `tab_supplier` (tên nhà cung cấp của đúng các lần mua được hiện;
     dòng sổ Misa mang sẵn `supplier_name` — thắng tên tra theo mã vì mã Misa không nằm trong `tab_supplier`).
Mốc sổ Misa được áp trong `latest_priced_by_code` (xem `product_price/misa_cutoff.py`).
ĐVT lấy ở danh mục sản phẩm, trống thì lấy ở lần mua gần nhất có ghi ĐVT.
Lần 1 = lần mua CÓ GIÁ gần nhất (bỏ dòng đơn giá 0); cùng ngày thì id lớn hơn là gần hơn. Khoảng ngày mua lọc TRƯỚC khi xếp
hạng (chỉ các lần mua trong khoảng mới được tính). Lọc nhà cung cấp / biến động / ngưỡng + xếp tại máy chủ (luật §8).
"""
import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.product.model import Product
from app.modules.product_price.latest_priced_query import latest_priced_by_code
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote
from app.modules.supplier.model import Supplier

from .cost_service import fold_text
from .bom_parts_service import usage_by_code
from .material_scope import material_codes
from .impact_service import OTHER_GROUP
from .numbers import iso, num
from .price_list_service import sort_rows

DEFAULT_N = 5
MAX_N = 10
#  khóa cột được phép xếp (whitelist); thêm `p{k}_price` / `p{k}_date` (k = 1..MAX_N) = đơn giá / ngày của lần thứ k
SORT_KEYS = {"code", "name", "group", "unit", "purchase_count", "last_price", "last_date", "v12", "v1n", "avg"}
_SLOT_KEY = re.compile(r"^p(\d{1,2})_(price|date)$")
TRENDS = ("all", "up", "down", "flat")
#  Thứ tự chip nhóm: thành phần của định mức theo đúng thứ tự cột, nhóm khác theo tên, "Khác" cuối cùng.
GROUP_ORDER = ("chai", "nap", "nhan", "nhan thung", "thung")
_VTBB_SUFFIX = re.compile(r"\s*-\s*VTBB\s*$", re.IGNORECASE)


def supplier_label(name: str | None, code: str) -> str:
    """Tên nhà cung cấp hiện trên ma trận: bỏ đuôi " - VTBB" (nhãn nội bộ của dữ liệu MISA); không có tên thì lấy mã."""
    return _VTBB_SUFFIX.sub("", (name or "").strip()) or code


def _ratio(newer: float | None, older: float | None) -> float | None:
    """Biến động `newer / older - 1` (tỷ số, 6 số lẻ); thiếu một vế hoặc mẫu số 0 thì None."""
    if newer is None or not older:
        return None
    return round(newer / older - 1, 6)


def _row(code: str, info: tuple[str, str, str], count: int, points: list[dict], names: dict[str, str], n: int) -> dict:
    purchases = [{"date": iso(p["date"]), "supplier_code": p["supplier_code"],
                  "supplier": supplier_label(p.get("supplier_name") or names.get(p["supplier_code"]), p["supplier_code"]),
                  "qty": num(p["qty"], 3), "price": num(p["price"])} for p in points]
    prices = [p["price"] for p in purchases]
    name, group, unit = info
    #  ĐVT danh mục thường để trống: lấy ĐVT của lần mua gần nhất có ghi ĐVT (đã nằm sẵn trong truy vấn xếp hạng).
    unit = unit or next((p["unit"] for p in points if p.get("unit")), "")
    return {"code": code, "name": name, "group": group or OTHER_GROUP, "unit": unit, "purchase_count": count,
            "purchases": purchases, "last_price": prices[0] if prices else None,
            "last_date": purchases[0]["date"] if purchases else None,
            "v12": _ratio(prices[0], prices[1]) if len(prices) > 1 else None,
            "v1n": _ratio(prices[0], prices[n - 1]) if len(prices) >= n else None,
            "avg": num(sum(prices) / len(prices)) if prices else None}


def _group_rank(group: str) -> tuple[int, int, str]:
    folded = fold_text(group)
    if folded in GROUP_ORDER:
        return 0, GROUP_ORDER.index(folded), ""
    return (2, 0, "") if group == OTHER_GROUP else (1, 0, folded)


def group_counts(rows: list[dict]) -> list[dict]:
    """`[{group, count}]` theo thứ tự chip (không kèm "Tất cả")."""
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["group"]] = counts.get(r["group"], 0) + 1
    return [{"group": g, "count": counts[g]} for g in sorted(counts, key=_group_rank)]


def supplier_options(rows: list[dict]) -> list[dict]:
    """`[{code, name}]` nhà cung cấp xuất hiện trong các lần mua đang hiện — cho ô chọn nhiều, xếp theo tên.

    Một mã NCC có thể mang nhiều tên (tên chép theo dòng Misa khác tên danh mục): chọn tên nhỏ nhất theo (chữ bỏ dấu, chữ gốc)
    để kết quả KHÔNG phụ thuộc thứ tự dòng đầu vào (trước đây tên cuối cùng duyệt được thắng, mà dòng đi ra từ một tập mã)."""
    labels: dict[str, set[str]] = {}
    for r in rows:
        for p in r["purchases"]:
            if p["supplier_code"]:
                labels.setdefault(p["supplier_code"], set()).add(p["supplier"])
    found = {c: min(names, key=lambda name: (fold_text(name), name)) for c, names in labels.items()}
    return [{"code": c, "name": found[c]} for c in sorted(found, key=lambda c: (fold_text(found[c]), c))]


def _haystack(row: dict) -> str:
    suppliers = " ".join(p["supplier"] for p in row["purchases"])
    return fold_text(f"{row['code']} {row['name']} {row['group']} {suppliers}")


def _direction(row: dict) -> str | None:
    """Chiều đổi giá lần 1 so lần 2 theo giá THÔ (không qua làm tròn tỷ số): up / down / flat; thiếu lần 2 thì None."""
    prices = [p["price"] for p in row["purchases"][:2]]
    if len(prices) < 2:
        return None
    return "up" if prices[0] > prices[1] else "down" if prices[0] < prices[1] else "flat"


def _sorted(rows: list[dict], sort_by: str, sort_dir: str) -> list[dict]:
    """Xếp theo khóa tĩnh hoặc theo lần thứ k (`p{k}_price|date`); khóa lạ rơi về mã."""
    m = _SLOT_KEY.match(sort_by)
    if m and 1 <= int(m[1]) <= MAX_N:
        k, field = int(m[1]) - 1, m[2]
        tmp = [{**r, "_slot": r["purchases"][k][field] if k < len(r["purchases"]) else None} for r in rows]
        return [{key: v for key, v in r.items() if key != "_slot"}
                for r in sort_rows(tmp, "_slot", sort_dir, {"_slot"})]
    return sort_rows(rows, sort_by, sort_dir, SORT_KEYS)


def build_last_prices(db: Session, *, n: int = DEFAULT_N, q: str = "", product_codes: list[str] | None = None,
                      groups: list[str] | None = None, only_priced: bool = True,
                      bom_only: bool = False, scope: str = "bom", suppliers: list[str] | None = None,
                      date_from: date | None = None, date_to: date | None = None, trend: str = "all",
                      min_pct: float | None = None, sort_by: str = "code", sort_dir: str = "asc", scope_cond=None) -> dict:
    """`{rows, groups, suppliers}`: toàn bộ dòng đã lọc + xếp (chưa cắt trang), số mã mỗi nhóm, nhà cung cấp để chọn.

    `n` = số lần mua hiển thị (2..MAX_N). `scope`: `bom` = mã thành phần của định mức ∪ mã có báo giá; `all` = mọi mã có
    lần mua có giá; `bom_only` = chỉ mã thành phần của định mức (thắng `scope`). `date_from` / `date_to` lọc các lần mua
    TRƯỚC khi xếp hạng. `product_codes` (ô chọn mã, 27/11/2026) chỉ giữ đúng các mã đó (rỗng = mọi mã). `suppliers` giữ dòng có nhà cung cấp đó trong `n` lần đang hiện. `groups` (tên nhóm, nhiều tên = HOẶC) giữ dòng thuộc một trong các nhóm đó. `trend` (all / up / down / flat) lọc
    chiều đổi giá lần 1 so lần 2; `min_pct` giữ dòng có |lần 1 so lần 2| >= min_pct (đơn vị %).
    `suppliers` tính trên tập đã lọc "chỉ mã có giá" nhưng CHƯA áp tìm / nhóm / nhà cung cấp / biến động (ô chọn đứng yên).
    `groups` = số mã mỗi nhóm SAU mọi bộ lọc trừ bộ lọc nhóm (tìm, nhà cung cấp, khoảng ngày, xu hướng, ngưỡng %) — chip khớp
    với số dòng bấm vào sẽ ra.
    """
    n = max(2, min(int(n), MAX_N))
    comps = set(usage_by_code(db))     # mã thành phần của mọi định mức (gom ở SQL, không kéo từng dòng định mức về)
    quoted = {c for (c,) in db.query(ProductPriceQuote.product_code).distinct().all()}
    #  bao-CR-800: màn VTBB không mang mã nguyên liệu — dòng sổ giá đã bị `scope_cond` lọc, còn mã chỉ có báo giá / nằm trong
    #  định mức thì lọc ở đây.
    materials = material_codes(db)
    comps, quoted = comps - materials, quoted - materials
    universe = comps if bom_only else comps | quoted
    codes = None if (scope == "all" and not bom_only) else universe

    conds = [L.price > 0]
    if date_from is not None:
        conds.append(L.price_date >= date_from)
    if date_to is not None:
        conds.append(L.price_date <= date_to)
    if scope_cond is not None:
        conds.append(scope_cond)
    latest = latest_priced_by_code(db, n, codes=codes, rank_conds=conds, agg_conds=conds, agg_cols=[func.count(L.id)])

    points: dict[str, list[dict]] = {}
    counts: dict[str, int] = {}
    for code, entry in latest.items():
        points[code] = [{"price": r.price, "qty": r.qty, "unit": r.unit, "date": r.price_date, "supplier_code": r.supplier_code,
                       "supplier_name": r.supplier_name}
                        for r in entry.rows]
        counts[code] = int(entry.stats[0])
    #  Chỉ mã có giá (mặc định): không dựng dòng cho hàng chục nghìn mã định mức chưa có lần mua nào rồi mới bỏ đi.
    all_codes = set(points) if only_priced else ((set(universe) | set(points)) if codes is None else set(universe))

    info = {c: (nm or "", g or "", u or "") for c, nm, g, u in
            db.query(Product.code, Product.name, Product.item_group, Product.unit).filter(Product.code.in_(all_codes or {""})).all()}
    supplier_codes = {p["supplier_code"] for pts in points.values() for p in pts if p["supplier_code"]}
    names = dict(db.query(Supplier.code, Supplier.name).filter(Supplier.code.in_(supplier_codes or {""})).all())

    rows = [_row(c, info.get(c, ("", "", "")), counts.get(c, 0), points.get(c, []), names, n) for c in sorted(all_codes)]
    if only_priced:
        rows = [r for r in rows if r["purchase_count"] > 0]
    supplier_list = supplier_options(rows)    # ô chọn nhà cung cấp đứng yên theo tập "chỉ mã có giá" (như bản mẫu)

    terms = fold_text(q).split()
    if terms:
        hay = {r["code"]: _haystack(r) for r in rows}
        rows = [r for r in rows if all(t in hay[r["code"]] for t in terms)]
    picked = {c.strip() for c in (product_codes or []) if c.strip()}
    if picked:
        rows = [r for r in rows if r["code"] in picked]
    wanted = {c for c in (suppliers or []) if c}
    if wanted:
        rows = [r for r in rows if any(p["supplier_code"] in wanted for p in r["purchases"])]
    if trend in ("up", "down", "flat"):
        rows = [r for r in rows if _direction(r) == trend]
    if min_pct:
        rows = [r for r in rows if r["v12"] is not None and abs(r["v12"]) * 100 >= min_pct - 1e-9]
    #  chip nhóm đếm trên tập đã qua MỌI bộ lọc trừ chính bộ lọc nhóm (cùng luật chip xu hướng của Tổng hợp)
    chips = group_counts(rows)
    #  nhiều nhóm = HOẶC (chip bật / tắt); so không dấu, không phân biệt hoa thường; chuỗi rỗng bị bỏ
    wanted_groups = {fold_text(g) for g in (groups or []) if g.strip()}
    if wanted_groups:
        rows = [r for r in rows if fold_text(r["group"]) in wanted_groups]
    return {"rows": _sorted(rows, sort_by, sort_dir), "groups": chips, "suppliers": supplier_list}


def flatten_for_export(row: dict, n: int = DEFAULT_N) -> dict:
    """Trải `purchases` thành khóa phẳng `p{k}_date|supplier|qty|price` (k = 1..n); biến động giữ TỶ SỐ (Excel hiện %)."""
    flat = dict(row)
    for k in range(1, n + 1):
        p = row["purchases"][k - 1] if k <= len(row["purchases"]) else {}
        flat[f"p{k}_date"], flat[f"p{k}_supplier"] = p.get("date"), p.get("supplier")
        flat[f"p{k}_qty"], flat[f"p{k}_price"] = p.get("qty"), p.get("price")
    return flat
