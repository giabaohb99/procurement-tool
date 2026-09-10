"""Báo cáo giá vốn lô hàng nhập khẩu (bao-CR-347).

HAI CÁCH ĐỌC cùng một lô hàng, và cả hai dùng chung một lần lọc đơn:

* **Theo lô** (`orders`) — một ĐƠN là một CỘT, mỗi chỉ tiêu là một DÒNG. Đọc dọc từ tiền
  hàng, qua từng loại chi phí, xuống tổng giá vốn và giá mỗi ký.
* **Theo dòng hàng** (`items`) — một MÃ HÀNG là một DÒNG, chi phí của lô đã chia về tới
  từng mã theo đúng cách chia khai trên khoản chi (bao-CR-319 P4), ra giá vốn mỗi đơn vị.

Backend trả mảng phẳng cho cả hai; việc xoay ngang/dọc là chuyện của màn hình và bản in,
để tab báo cáo, bản in ký tay và file Excel dùng CHUNG một con số.

Tên chi phí lấy nguyên danh mục `ImportCostType` của hệ thống — không gom nhóm lại theo
mẫu giấy, vì thu mua gõ chi phí theo danh mục đó và báo cáo phải soi ngược về được.

Tên các chỉ tiêu còn lại cũng lấy theo TRƯỜNG của đơn mua hàng chứ không chép mẫu giấy:
mẫu giấy viết "Giá đô" vì lô hàng của họ toàn mua bằng đô, còn đơn ở đây khai đồng tiền
riêng (JPY, CNY, EUR…) nên chỉ tiêu là "Tiền hàng (nguyên tệ)" kèm một dòng đồng tiền.

Số liệu tính BAY mỗi lần xem, không lưu — cùng ranh giới với bao-CR-319 P4: giá vốn phân bổ
chỉ để xem, không ghi vào kho, không ghi vào giá nhập.
"""
from sqlalchemy.orm import Session

from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import (DEFAULT_CURRENCY, IMPORT_COST_TYPE_LABELS,
                                              ImportCostType, OrderType, POImportCost, POItem,
                                              PurchaseOrder)

# Trạng thái đơn — nhãn tiếng Việt chỉ ở tầng hiển thị, nhưng bản in và file Excel không
# chạy qua giao diện nên phải có nhãn ngay tại đây.
PO_STATUS_LABELS = {
    "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
    "partial": "Đã nhận một phần", "received": "Đã nhận đủ", "completed": "Hoàn thành",
    "rejected": "Bị trả lại", "cancelled": "Đã từ chối", "processing": "Đang xử lý",
}


def _cost_type(raw) -> int:
    """Mã loại chi phí, mã lạ dồn về "Chi phí khác" thay vì rơi ra ngoài bảng."""
    try:
        return int(ImportCostType(int(raw or 0)))
    except ValueError:
        return int(ImportCostType.OTHER)


def _item_dict(it: POItem) -> dict:
    """Dòng hàng đúng dạng `allocate_import_costs` cần (khóa như `_item()` của ĐMH)."""
    qty = float(it.qty_order or 0)
    return {"id": it.id, "product_code": it.product_code or "", "product_name": it.product_name or "",
            "unit": it.unit or "", "qty_order": qty, "weight_kg": float(it.weight_kg or 0),
            "currency": (it.currency or "").strip().upper(),
            # `order_total` NGUYÊN TỆ đã gồm VAT dòng — cùng công thức với `order_total` của ĐMH
            "order_total": round(qty * float(it.price or 0) * (1 + float(it.vat or 0) / 100), 2),
            "exchange_rate": po_service.rate_of(it)}


def _cost_dict(c: POImportCost) -> dict:
    """Khoản chi phí đúng dạng `allocate_import_costs` cần, tiền đã quy đổi VNĐ."""
    ct = _cost_type(c.cost_type)
    return {"id": c.id, "cost_type": ct,
            "cost_type_label": IMPORT_COST_TYPE_LABELS.get(ImportCostType(ct), ""),
            "description": c.description or "",
            "supplier_code": c.supplier_code or "", "supplier_name": c.supplier_name or "",
            "base_amount": po_service.import_cost_base(c),
            "allocation_method": int(c.allocation_method or 0),
            "allocation_target": c.allocation_target or "",
            "manual_allocation": getattr(c, "manual_allocation", "")}


def _cost_type_columns(used: set[int]) -> list[dict]:
    """Danh sách loại chi phí BÀY RA — chỉ loại có phát sinh, theo thứ tự danh mục.

    Loại nào không đơn nào trong lần lọc này dùng tới thì không hiện: bảng đã rộng sẵn vì
    mỗi đơn một cột, thêm mười dòng 0 đồng là đẩy phần đọc được ra khỏi tờ giấy.
    Đánh số 2.1, 2.2… theo đúng thứ tự bày, để bản in gọi tên được từng dòng.
    """
    out = []
    for ct in IMPORT_COST_TYPE_LABELS:
        if int(ct) in used:
            out.append({"code": int(ct), "no": f"2.{len(out) + 1}",
                        "label": IMPORT_COST_TYPE_LABELS[ct]})
    return out


def _empty_by_type(codes: list[int]) -> dict:
    return {str(c): 0.0 for c in codes}


def _pick_orders(db: Session, po_ids: list[int], codes: list[str],
                 date_from: str, date_to: str, company_id: str | None) -> list[PurchaseOrder]:
    """Chọn đơn NHẬP KHẨU theo mã đơn (ưu tiên) hoặc theo khoảng ngày đặt.

    Khách chọn đúng vài mã đơn để in, nên `po_ids`/`codes` đứng trước; khoảng ngày chỉ là
    đường vào cho tab báo cáo. Nháp và đơn đã hủy/từ chối vẫn LẤY khi được gọi đích danh —
    giá vốn của đơn nháp chính là thứ thu mua cần xem trước khi trình.
    """
    q = db.query(PurchaseOrder).filter(PurchaseOrder.order_type == int(OrderType.IMPORT))
    if po_ids:
        q = q.filter(PurchaseOrder.id.in_(po_ids))
    elif codes:
        q = q.filter(PurchaseOrder.code.in_(codes))
    else:
        if date_from:
            q = q.filter(PurchaseOrder.order_date >= date_from)
        if date_to:
            q = q.filter(PurchaseOrder.order_date <= date_to)
    if company_id:
        q = q.filter(PurchaseOrder.company_id == int(company_id))
    return q.order_by(PurchaseOrder.order_date.asc(), PurchaseOrder.id.asc()).all()


def compute(db: Session, *, po_ids: list[int] | None = None, codes: list[str] | None = None,
            date_from: str = "", date_to: str = "", company_id: str | None = None) -> dict:
    """Dựng dữ liệu báo cáo giá vốn cho các đơn nhập khẩu đã chọn — cả hai cách đọc.

    Nạp dòng hàng và dòng chi phí của CẢ NHÓM đơn bằng hai truy vấn IN, không lặp từng đơn —
    báo cáo này in một lúc cả chục đơn.
    """
    orders = _pick_orders(db, po_ids or [], codes or [], date_from, date_to, company_id)
    ids = [p.id for p in orders]
    items_by_po: dict[int, list[POItem]] = {i: [] for i in ids}
    costs_by_po: dict[int, list[POImportCost]] = {i: [] for i in ids}
    if ids:
        for it in db.query(POItem).filter(POItem.po_id.in_(ids)).order_by(POItem.id.asc()).all():
            items_by_po.setdefault(it.po_id, []).append(it)
        for c in db.query(POImportCost).filter(POImportCost.po_id.in_(ids)).order_by(POImportCost.id.asc()).all():
            costs_by_po.setdefault(c.po_id, []).append(c)

    # Loại chi phí nào có mặt trong lần lọc này — quyết định bộ dòng/cột của cả hai tab.
    used = {_cost_type(c.cost_type) for rows in costs_by_po.values() for c in rows}
    cost_types = _cost_type_columns(used)
    type_codes = [g["code"] for g in cost_types]

    out: list[dict] = []
    item_rows: list[dict] = []
    warnings: list[str] = []
    for po in orders:
        items = [_item_dict(it) for it in items_by_po.get(po.id, [])]
        costs = [_cost_dict(c) for c in costs_by_po.get(po.id, [])]
        qty_total = round(sum(it["qty_order"] for it in items), 3)
        weight_total = round(sum(it["weight_kg"] for it in items), 3)
        # Tiền hàng theo SL ĐẶT, ĐÃ gồm VAT dòng — cùng công thức với `order_total` của đơn.
        goods_amount = round(sum(it["order_total"] for it in items), 2)
        # Từng DÒNG hàng khai được đồng tiền riêng, nên ngay trong một đơn cũng có thể lẫn
        # USD với VND. Lẫn thì ô nguyên tệ của đơn đó vô nghĩa — đánh dấu để bỏ trống.
        po_currency = (po.currency or "").strip().upper() or DEFAULT_CURRENCY
        currency_mixed = bool({it["currency"] for it in items if it["currency"]} - {po_currency})
        goods_base = round(sum(it["order_total"] * it["exchange_rate"] for it in items), 2)

        by_type = _empty_by_type(type_codes)
        for c in costs:
            by_type[str(c["cost_type"])] = round(by_type[str(c["cost_type"])] + c["base_amount"], 2)
        cost_total = round(sum(by_type.values()), 2)

        row = {
            "po_id": po.id, "code": po.code, "order_date": po.order_date or "",
            "etd_date": po.etd_date or "",                   # ngày hàng rời cảng xuất
            "status": po.status or "",
            "status_label": PO_STATUS_LABELS.get(po.status or "", po.status or ""),
            "note": po.note or "",
            "supplier_code": po.supplier_code or "", "supplier_name": po.supplier_name or "",
            "customs_decl_no": po.customs_decl_no or "", "customs_decl_date": po.customs_decl_date or "",
            "currency": po_currency, "currency_mixed": currency_mixed,
            "exchange_rate": po_service.rate_of(po),
            "qty_total": qty_total, "weight_total": weight_total,
            "goods_amount": goods_amount,                    # tiền hàng NGUYÊN TỆ của đơn
            "goods_base": goods_base,                        # tiền hàng đã quy đổi VNĐ
            "by_type": by_type, "cost_total": cost_total,
            "landed_total": round(goods_base + cost_total, 2),
        }
        # Chưa khai kg thì để 0 chứ không chia — chia cho 0 là vỡ, mà đoán 1kg còn tệ hơn.
        row["price_per_kg"] = round(row["landed_total"] / weight_total, 2) if weight_total > 0 else 0.0
        out.append(row)
        item_rows.extend(_order_item_rows(po, items, costs, type_codes, warnings))

    return {"cost_types": cost_types, "orders": out, "totals": _totals(out, type_codes),
            "items": item_rows, "item_totals": _item_totals(item_rows, type_codes),
            "warnings": warnings}


def _order_item_rows(po: PurchaseOrder, items: list[dict], costs: list[dict],
                     type_codes: list[int], warnings: list[str]) -> list[dict]:
    """Tab "theo dòng hàng" của MỘT đơn — chia chi phí về từng mã hàng rồi gom theo loại.

    Chia bằng đúng `allocate_import_costs` của ĐMH chứ không tự cộng lại: cách chia (theo
    giá trị / khối lượng / số lượng / chỉ định / nhập tay) khai trên từng khoản, và bản in
    Đơn mua hàng nhập khẩu đang bày đúng con số đó — hai nơi lệch nhau là kế toán mất buổi.
    """
    alloc = po_service.allocate_import_costs(items, costs)
    for w in alloc.get("warnings", []):
        warnings.append(f"{po.code}: {w}")
    rows = []
    for line in alloc.get("lines", []):
        by_type = _empty_by_type(type_codes)
        for c in line.get("costs", []):
            key = str(_cost_type(c.get("cost_type")))
            if key in by_type:
                by_type[key] = round(by_type[key] + float(c.get("base_amount") or 0), 2)
        qty = float(line.get("qty_order") or 0)
        weight = float(line.get("weight_kg") or 0)
        landed = float(line.get("landed_base") or 0)
        rows.append({
            "po_id": po.id, "code": po.code, "etd_date": po.etd_date or "",
            "status_label": PO_STATUS_LABELS.get(po.status or "", po.status or ""),
            "item_id": line.get("item_id"),
            "product_code": line.get("product_code") or "", "product_name": line.get("product_name") or "",
            "unit": line.get("unit") or "", "qty_order": qty, "weight_kg": weight,
            "goods_base": float(line.get("goods_base") or 0),
            "by_type": by_type, "cost_base": float(line.get("cost_base") or 0),
            "landed_base": landed,
            # Giá vốn MỘT đơn vị hàng — con số cuối cùng người ta mở báo cáo này để tìm.
            "price_per_unit": round(landed / qty, 2) if qty > 0 else 0.0,
            "price_per_kg": round(landed / weight, 2) if weight > 0 else 0.0,
        })
    return rows


def _totals(rows: list[dict], type_codes: list[int]) -> dict:
    """Cột TỔNG của tab theo lô. Giá/Kg tính lại từ tổng tiền / tổng kg, KHÔNG cộng dồn
    giá/kg của từng đơn — cộng giá đơn vị lại với nhau là một con số vô nghĩa.

    Tiền nguyên tệ chỉ cộng khi cả nhóm đơn chung MỘT đồng tiền và không đơn nào lẫn đồng
    tiền ở dòng hàng: lọc trúng một đơn yên và một đơn đô rồi cộng thẳng hai con số đó lại
    là ra một số không thuộc đồng tiền nào.
    Cột VNĐ thì cộng bình thường vì đã quy đổi qua tỷ giá của từng dòng.
    """
    weight = round(sum(r["weight_total"] for r in rows), 3)
    goods_base = round(sum(r["goods_base"] for r in rows), 2)
    by_type = _empty_by_type(type_codes)
    for r in rows:
        for k in by_type:
            by_type[k] = round(by_type[k] + r["by_type"].get(k, 0.0), 2)
    cost_total = round(sum(by_type.values()), 2)
    landed_total = round(goods_base + cost_total, 2)
    currencies = {r["currency"] for r in rows if r["currency"]}
    mixed = len(currencies) > 1 or any(r["currency_mixed"] for r in rows)
    return {"qty_total": round(sum(r["qty_total"] for r in rows), 3),
            "weight_total": weight,
            "currency": "" if mixed else next(iter(currencies), ""),
            "currency_mixed": mixed,
            "goods_amount": 0.0 if mixed else round(sum(r["goods_amount"] for r in rows), 2),
            "goods_base": goods_base, "order_count": len(rows),
            "by_type": by_type, "cost_total": cost_total, "landed_total": landed_total,
            "price_per_kg": round(landed_total / weight, 2) if weight > 0 else 0.0}


def _item_totals(rows: list[dict], type_codes: list[int]) -> dict:
    """Dòng TỔNG của tab theo dòng hàng. Không có giá vốn/đơn vị: mỗi dòng một đơn vị tính
    khác nhau, cộng cái kg với cái cái rồi chia ra là số không đọc được."""
    by_type = _empty_by_type(type_codes)
    for r in rows:
        for k in by_type:
            by_type[k] = round(by_type[k] + r["by_type"].get(k, 0.0), 2)
    weight = round(sum(r["weight_kg"] for r in rows), 3)
    landed = round(sum(r["landed_base"] for r in rows), 2)
    return {"line_count": len(rows), "qty_order": round(sum(r["qty_order"] for r in rows), 3),
            "weight_kg": weight, "goods_base": round(sum(r["goods_base"] for r in rows), 2),
            "by_type": by_type, "cost_base": round(sum(r["cost_base"] for r in rows), 2),
            "landed_base": landed,
            "price_per_kg": round(landed / weight, 2) if weight > 0 else 0.0}
