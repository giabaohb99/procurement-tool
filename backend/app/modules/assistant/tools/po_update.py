"""ai-CR-241 — phần riêng ĐƠN MUA HÀNG (ĐMH) của `propose_document_update` / `confirm_update`.

Đại ca duyệt 16/11/2026 sau vụ PO01178 (tạo trên v2: trống kho, đơn giá về 0, phải chạy script trên prod mới sửa được).
Trợ lý / cổng MCP được ĐỀ XUẤT sửa đơn đang Nháp hoặc Bị trả lại:

- đầu đơn: ghi chú, hình thức thanh toán NCC (khai ở `update_tool._ENTITY_RULES`);
- từng dòng (`po_lines`): đơn giá, VAT, SL đặt, kho nhận, tên trên hóa đơn, ngày yêu cầu / dự kiến có hàng, ghi chú.
  Nhận dạng dòng bằng `line_id` (id dòng, `procurement_doc_read` trả kèm) hoặc `product_code` khi mã không trùng trên
  đơn; `all_lines` áp một giá trị cho mọi dòng (kho, VAT, hai ngày, ghi chú — không áp đơn giá / SL / tên hóa đơn).
  KHÔNG thêm / bỏ dòng ở đợt này.

Ghi: dựng lại ĐỦ danh sách dòng từ sổ (kèm lần giao — thiếu là `_save_items` xóa lần giao) rồi đi đúng
`purchase_order.edit_service.update_po` như nút Lưu trên web. Thao tác trong token theo ID dòng; lúc xác nhận kiểm lại
mọi giá trị (kho còn trong danh mục, luật VAT đơn nhập khẩu, trần số) — token chỉ là tờ đề xuất.
"""
from __future__ import annotations

from fastapi import HTTPException
from pydantic import ValidationError

from .draft_tool import _clean_text, _iso_date

MAX_PO_LINE_OPS = 20
MAX_PRICE = 1_000_000_000_000      # cột Numeric(18, 4)
MAX_QTY = 1_000_000_000
PRICE_DRIFT = 0.20                 # lệch giá đề xuất trên YCMH nguồn quá 20% thì cảnh báo
EMPTY = "(trống)"

#  Trường dòng sửa được → nhãn trên bảng cũ → mới (đúng chữ cột trên màn ĐMH).
LINE_FIELDS: dict[str, str] = {
    "price": "Đơn giá",
    "vat": "VAT %",
    "qty_order": "SL đặt",
    "warehouse_code": "Kho nhận",
    "invoice_name": "Tên trên hóa đơn",
    "required_date": "Ngày yêu cầu có hàng",
    "expected_date": "Ngày dự kiến có hàng",
    "note": "Ghi chú dòng",
}
#  Áp được cho mọi dòng một lượt (`all_lines`) — giá, số lượng, tên hóa đơn thì khác nhau từng dòng.
ALL_LINES_FIELDS = ("warehouse_code", "vat", "required_date", "expected_date", "note")
_NUMBERS = ("price", "vat", "qty_order")
_DATES = ("required_date", "expected_date")
_TEXT_MAX = {"invoice_name": 255, "note": 355}
_DONE = ("completed", "cancelled")   # dòng Hoàn thành / Hủy: `_save_items` bỏ qua nguyên dòng

PO_LINES_PARAM = {
    "type": "array",
    "description": "Sửa DÒNG HÀNG của ĐƠN MUA HÀNG (chỉ entity=purchase_order). Mỗi phần tử sửa MỘT dòng: nhận dạng "
                   "bằng line_id (id dòng — procurement_doc_read trả trong `lines[].line_id`) hoặc product_code khi mã "
                   "đó chỉ có một dòng trên đơn; hoặc all_lines=true để đặt cùng một giá trị cho MỌI dòng (chỉ kho, "
                   "VAT, hai ngày, ghi chú). Chỉ điền trường người dùng muốn đổi. Không thêm / bỏ dòng.",
    "items": {
        "type": "object",
        "properties": {
            "line_id": {"type": "integer", "description": "Id dòng trên đơn (ưu tiên)."},
            "product_code": {"type": "string", "description": "Mã hàng của dòng (khi mã không trùng trên đơn)."},
            "all_lines": {"type": "boolean", "description": "true = áp cho mọi dòng."},
            "price": {"type": "number", "description": "Đơn giá mới TRƯỚC VAT, theo loại tiền của đơn, >= 0."},
            "price_after_vat": {"type": "number",
                                "description": "Đơn giá mới ĐÃ GỒM VAT (người dùng nói giá sau thuế) — máy tự tính đơn giá "
                                               "trước VAT theo VAT của dòng (hoặc `vat` gửi kèm), giữ 4 số lẻ. KHÔNG tự "
                                               "chia nhẩm; không gửi cùng `price`."},
            "vat": {"type": "number", "description": "% VAT mới, 0 đến dưới 100. Đơn nhập khẩu luôn 0."},
            "qty_order": {"type": "number", "description": "SL đặt NCC mới, >= 0."},
            "warehouse_code": {"type": "string", "description": "Kho nhận: mã HOẶC tên kho trong danh mục."},
            "invoice_name": {"type": "string", "description": "Tên trên hóa đơn mới."},
            "required_date": {"type": "string", "description": "Ngày yêu cầu có hàng, YYYY-MM-DD."},
            "expected_date": {"type": "string", "description": "Ngày dự kiến có hàng, YYYY-MM-DD."},
            "note": {"type": "string", "description": "Ghi chú dòng mới."},
        },
    },
}


# ── Đọc ─────────────────────────────────────────────────────────────────────────────────

def lines_of(db, po_id: int) -> list:
    from app.modules.purchase_order.base_service import items_of
    return items_of(db, po_id)


def _is_import(po) -> bool:
    from app.modules.purchase_order.model import OrderType
    return int(po.order_type or OrderType.DOMESTIC) == int(OrderType.IMPORT)


def _currency(po) -> str:
    return (po.currency or "").strip() or "VND"


def _value(row, field: str):
    value = getattr(row, field, None)
    if field in _NUMBERS:
        return float(value or 0)
    return str(value or "").strip()


def line_state(db, po) -> list:
    """Giá trị hiện tại của mọi ô sửa được trên mọi dòng — vào dấu trạng thái của đề xuất (`_state_sig`)."""
    return [[r.id, *[_value(r, f) for f in LINE_FIELDS]] for r in lines_of(db, po.id)]


def _num_text(value: float) -> str:
    text = f"{value:,.4f}".rstrip("0").rstrip(".")
    return text.replace(",", "#").replace(".", ",").replace("#", ".")


def _money(value: float) -> str:
    return _num_text(round(value, 2))


def _shown(field: str, value, warehouses: dict) -> str:
    if field in _NUMBERS:
        return _num_text(float(value or 0))
    if field == "warehouse_code" and value:
        name = warehouses.get(value)
        return f"{value} · {name}" if name else value
    return value if value else EMPTY


def _warehouse_names(db) -> dict:
    from app.modules.catalog.model import Warehouse
    return {w.code: w.name for w in db.query(Warehouse).all()}


def _find_warehouse(db, wanted: str) -> tuple[str | None, str | None]:
    """Kho ĐANG DÙNG khớp đúng mã hoặc tên (không phân biệt hoa thường) → (mã, lỗi)."""
    from app.modules.catalog.model import Warehouse

    key = (wanted or "").strip().lower()
    rows = db.query(Warehouse).filter(Warehouse.is_active.is_(True)).order_by(Warehouse.code).all()
    by_code = [w for w in rows if (w.code or "").lower() == key]
    by_name = [w for w in rows if (w.name or "").strip().lower() == key]
    found = by_code or by_name
    if key and len(found) == 1:
        return found[0].code, None
    listed = "; ".join(f"{w.code} ({w.name})" for w in rows[:30])
    if len(found) > 1:
        return None, f"Có nhiều kho tên **{wanted}** — dùng mã kho: {listed}."
    return None, f"Không có kho **{wanted}** trong danh mục kho đang dùng. Các kho hiện có: {listed}."


def _pr_prices(db, po) -> dict[str, float]:
    """Giá đề xuất (trước VAT) theo mã hàng trên YCMH nguồn — để cảnh báo lệch giá. Đơn ngoại tệ thì không so."""
    if not (po.pr_code or "").strip() or _currency(po) != "VND":
        return {}
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    pr = (db.query(PurchaseRequest)
          .filter(PurchaseRequest.code == po.pr_code, PurchaseRequest.is_deleted.is_(False)).first())
    if pr is None:
        return {}
    rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    return {(r.product_code or "").strip(): float(r.price or 0) for r in rows if float(r.price or 0) > 0}


def price_before_vat(price_after_vat: float, vat) -> float:
    """Đơn giá trước VAT từ giá đã gồm VAT — nhân / chia theo (100 + VAT), giữ 4 số lẻ, ĐÚNG công thức hai giao diện
    (`frontend-v2/.../utils/vat-price.ts`, `frontend/src/utils/vatPrice.ts`, duoc-CR-776). VAT âm / rỗng coi như 0."""
    rate = float(vat or 0)
    rate = rate if rate > 0 else 0.0
    return round(float(price_after_vat) * 100 / (100 + rate), 4)


# ── Kiểm một giá trị ────────────────────────────────────────────────────────────────────

def _clean_value(db, po, field: str, raw) -> tuple[object, str | None]:
    label = LINE_FIELDS[field]
    if field in _NUMBERS:
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            return None, f"{label} phải là số."
        try:
            value = float(raw)
        except ValueError:
            return None, f"{label} phải là số."
        if field == "vat":
            if not 0 <= value < 100:
                return None, "VAT % chỉ nhận từ 0 tới dưới 100."
            if value and _is_import(po):
                return None, (f"Đơn {po.code} là đơn nhập khẩu — VAT dòng hàng luôn bằng 0 (thuế GTGT hàng nhập khai ở "
                              "bảng chi phí nhập khẩu), không đặt được VAT khác 0.")
            return value, None
        cap = MAX_PRICE if field == "price" else MAX_QTY
        if not 0 <= value <= cap:
            return None, f"{label} phải từ 0 tới {_num_text(cap)}."
        return value, None
    if field in _DATES:
        value = _iso_date(raw)
        if value is None:
            return None, f"{label} sai định dạng — cần YYYY-MM-DD, hỏi lại người dùng."
        return value, None
    if field == "warehouse_code":
        return _find_warehouse(db, _clean_text(raw, 255))
    return _clean_text(raw, _TEXT_MAX[field]), None


# ── Bước đề xuất ────────────────────────────────────────────────────────────────────────

def _pick_rows(rows: list, op: dict, index: int) -> tuple[list, str | None]:
    if op.get("all_lines") is True:
        return list(rows), None
    line_id = op.get("line_id")
    if line_id is not None:
        if isinstance(line_id, bool) or not isinstance(line_id, int):
            return [], f"Dòng sửa thứ {index}: line_id phải là số."
        found = [r for r in rows if r.id == line_id]
        if not found:
            return [], f"Đơn không có dòng line_id={line_id} — tra lại đơn (procurement_doc_read) lấy đúng line_id."
        return found, None
    code = _clean_text(op.get("product_code"), 50)
    if not code:
        return [], f"Dòng sửa thứ {index}: cần line_id hoặc product_code (hoặc all_lines=true)."
    found = [r for r in rows if (r.product_code or "").strip().upper() == code.upper()]
    if not found:
        return [], f"Đơn không có dòng mã hàng **{code}** — tra lại đơn rồi hỏi người dùng đúng dòng nào."
    if len(found) > 1:
        ids = ", ".join(str(r.id) for r in found)
        return [], (f"Mã hàng **{code}** có {len(found)} dòng trên đơn (line_id {ids}) — phải dùng line_id để chỉ đúng "
                    "dòng, hỏi người dùng sửa dòng nào.")
    return found, None


def clean_po_lines(db, po, raw) -> tuple[list[dict], list[dict], list[str], str | None]:
    """`po_lines` của model → (thao tác theo id dòng, các dòng bảng cũ → mới, cảnh báo, lỗi)."""
    if raw in (None, []):
        return [], [], [], None
    if not isinstance(raw, list):
        return [], [], [], "po_lines phải là danh sách."
    if len(raw) > MAX_PO_LINE_OPS:
        return [], [], [], f"Quá {MAX_PO_LINE_OPS} dòng sửa một lần — báo người dùng mở đơn sửa tay."
    rows = lines_of(db, po.id)
    order = {r.id: i + 1 for i, r in enumerate(rows)}
    wanted: dict[int, dict] = {}
    for index, op in enumerate(raw, start=1):
        if not isinstance(op, dict):
            return [], [], [], f"Dòng sửa thứ {index} sai định dạng."
        unknown = [k for k in op if k not in LINE_FIELDS
                   and k not in ("line_id", "product_code", "all_lines", "price_after_vat")]
        if unknown:
            allowed = ", ".join(LINE_FIELDS)
            return [], [], [], (f"Trường {', '.join(unknown)} KHÔNG sửa được qua trợ lý trên dòng ĐMH (chỉ: {allowed}) — "
                                "báo người dùng mở đơn sửa tay.")
        fields = [f for f in LINE_FIELDS if f in op]
        post_vat = None
        if "price_after_vat" in op:
            #  duoc-CR-776: người dùng nói giá đã gồm VAT — máy tính ngược, cùng công thức màn hình (giữ 4 số lẻ).
            if "price" in op:
                return [], [], [], "Chỉ gửi một trong hai: price (trước VAT) hoặc price_after_vat (đã gồm VAT)."
            if op.get("all_lines") is True:
                return [], [], [], "price_after_vat phải sửa từng dòng, không áp cho mọi dòng."
            post_vat, post_error = _clean_value(db, po, "price", op.get("price_after_vat"))
            if post_error:
                return [], [], [], post_error
        if not fields and post_vat is None:
            return [], [], [], f"Dòng sửa thứ {index} không có trường nào để đổi."
        if op.get("all_lines") is True:
            bad = [f for f in fields if f not in ALL_LINES_FIELDS]
            if bad:
                return [], [], [], (f"all_lines chỉ áp được cho {', '.join(ALL_LINES_FIELDS)} — {', '.join(bad)} phải "
                                    "sửa từng dòng.")
        targets, pick_error = _pick_rows(rows, op, index)
        if pick_error:
            return [], [], [], pick_error
        values = {}
        for field in fields:
            value, value_error = _clean_value(db, po, field, op.get(field))
            if value_error:
                return [], [], [], value_error
            values[field] = value
        for row in targets:
            if (row.progress_status or "") in _DONE:
                return [], [], [], (f"Dòng {order[row.id]} ({row.product_code}) đã Hoàn thành / Hủy — không sửa được, "
                                    "kể cả trên web.")
            row_values = dict(values)
            if post_vat is not None:
                row_values["price"] = price_before_vat(post_vat, values.get("vat", _value(row, "vat")))
            wanted.setdefault(row.id, {}).update(row_values)
    return _build_view(db, po, rows, order, wanted)


def _build_view(db, po, rows, order, wanted) -> tuple[list[dict], list[dict], list[str], str | None]:
    warehouses = _warehouse_names(db)
    pr_prices = _pr_prices(db, po)
    currency = _currency(po)
    ops: list[dict] = []
    view: list[dict] = []
    warnings: list[str] = []
    for row in rows:
        values = {f: v for f, v in (wanted.get(row.id) or {}).items() if v != _value(row, f)}
        if not values:
            continue
        ops.append({"id": row.id, "set": values})
        head = f"Dòng {order[row.id]} · {row.product_code or row.product_name or '#' + str(row.id)}"
        for field, new in values.items():
            view.append({"field": f"po_line_{row.id}_{field}", "label": f"{head} · {LINE_FIELDS[field]}",
                         "old": _shown(field, _value(row, field), warehouses), "new": _shown(field, new, warehouses)})
        if values.keys() & set(_NUMBERS):
            old_q, old_p, old_v = (_value(row, f) for f in ("qty_order", "price", "vat"))
            new_q, new_p, new_v = (values.get(f, _value(row, f)) for f in ("qty_order", "price", "vat"))
            view.append({"field": f"po_line_{row.id}_amount", "label": f"{head} · Giá trị đặt (trước / sau VAT)",
                         "old": f"{_money(old_q * old_p)} / {_money(old_q * old_p * (1 + old_v / 100))} {currency}",
                         "new": f"{_money(new_q * new_p)} / {_money(new_q * new_p * (1 + new_v / 100))} {currency}"})
        suggested = pr_prices.get((row.product_code or "").strip())
        if "price" in values and suggested:
            drift = abs(values["price"] - suggested) / suggested
            if drift > PRICE_DRIFT:
                warnings.append(f"{head}: đơn giá mới {_num_text(values['price'])} lệch {round(drift * 100)}% so với "
                                f"giá đề xuất {_num_text(suggested)} trên {po.pr_code} — hỏi lại người dùng cho chắc.")
    return ops, view, warnings, None


# ── Bước xác nhận ───────────────────────────────────────────────────────────────────────

def check_po_ops(db, po, raw) -> list[dict]:
    """Thao tác lấy từ token: kiểm lại hình dạng + từng giá trị như lúc đề xuất. Sai → 400, không ghi."""
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > len(lines_of(db, po.id)) or len(raw) > 500:
        raise HTTPException(400, "Đề xuất sửa dòng không hợp lệ.")
    known = {r.id for r in lines_of(db, po.id)}
    clean = []
    for op in raw:
        values = op.get("set") if isinstance(op, dict) else None
        if not isinstance(op, dict) or op.get("id") not in known or not isinstance(values, dict) \
                or not values or not set(values) <= set(LINE_FIELDS):
            raise HTTPException(400, "Dòng hàng trên đơn đã đổi sau lúc đề xuất, hoặc đề xuất không hợp lệ — nhờ trợ "
                                     "lý soạn lại đề xuất mới.")
        checked = {}
        for field, value in values.items():
            clean_value, error = _clean_value(db, po, field, value)
            if error:
                raise HTTPException(400, error)
            checked[field] = clean_value
        clean.append({"id": op["id"], "set": checked})
    return clean


def build_items(db, po, ops: list[dict]) -> list:
    """Danh sách dòng ĐẦY ĐỦ đúng hình form gửi lên (`POItemIn` kèm lần giao), chỉ đổi các ô trong `ops`."""
    from decimal import Decimal

    from app.modules.purchase_order.base_service import deliveries_of
    from app.modules.purchase_order.schema import DeliveryIn, POItemIn

    def as_input(cls, row, skip=()):
        data = {}
        for name in cls.model_fields:
            if name in skip:
                continue
            value = getattr(row, name, None)
            if value is not None:
                data[name] = float(value) if isinstance(value, Decimal) else value
        return data

    changes = {o["id"]: o["set"] for o in ops}
    try:
        items = []
        for row in lines_of(db, po.id):
            data = as_input(POItemIn, row, skip=("deliveries",))
            data.update(changes.get(row.id, {}))
            data["deliveries"] = [DeliveryIn(**as_input(DeliveryIn, d)) for d in deliveries_of(db, row.id)]
            items.append(POItemIn(**data))
    except ValidationError as e:
        raise HTTPException(400, "Đơn có dòng dữ liệu cũ không hợp lệ nên trợ lý không sửa được — mở đơn sửa tay.") from e
    return items


def write_po(db, user, po, fields: dict, ops: list[dict]) -> None:
    """Ghi qua ĐÚNG `update_po` (cùng đường nút Lưu): đầu đơn chỉ các ô được đổi, dòng thì gửi đủ danh sách."""
    from app.modules.purchase_order.edit_service import update_po
    from app.modules.purchase_order.schema import POUpdate

    payload = dict(fields)
    if ops:
        payload["items"] = build_items(db, po, ops)
    update_po(db, po.id, POUpdate(**payload), user.id)
