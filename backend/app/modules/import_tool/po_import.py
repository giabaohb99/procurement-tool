"""Import Đơn mua hàng — sheet 6 "TIẾN ĐỘ MUA HÀNG" (header dòng 4, data từ dòng 5).

Khoá gom:
  Mã Misa (J)                    -> PurchaseOrder
    └ (Mã SP L + Số HĐ AE)       -> POItem  (số HĐ thuộc dòng hàng)
        └ mỗi dòng Excel         -> PODelivery
Sau khi dựng PO+dòng+lần giao -> recompute_effects() tự sinh nhập kho + tồn + công nợ.
Dòng "Hoàn thành" -> tạo YCTT + ghi ĐÃ CHI (chỉ ở chế độ Ghi).
"""
import json
from datetime import datetime

from sqlalchemy import inspect as sa_inspect

from app.modules.catalog.model import ItemGroup, Unit, Warehouse
from app.modules.company.model import Company
from app.modules.payable.model import Payable
from app.modules.payment_request import service as pr_service
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.product.model import Product
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PODelivery, PurchaseOrder
from app.modules.supplier.model import Supplier

from .model import ImportBatch, ImportStatus, LogLevel
from .survey_import import _b, _cell, _d, _fit, _n, _ncode, _persist, _s, _vat

HEADER_ROW = 4
DATA_START = 5


def _scode(v) -> str:
    """Mã dạng số (Số HĐ, Misa...) — Excel lưu số nên openpyxl đọc float 779.0; cắt '.0'."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    return _s(v)

# tên cột "Trạng thái" (P) -> progress_status chuẩn của POItem
_PROGRESS = {
    "hoàn thành": "Hoàn thành", "đã nhận": "Đã nhận hàng", "đang giao": "Đang giao hàng",
    "đã đặt hàng": "Đã đặt hàng", "chưa đặt hàng": "Chưa đặt hàng", "hủy đơn": "Hủy đơn",
    "tạm ngưng": "Tạm ngưng", "đã đặt": "Đã đặt hàng",
}


def _last_row(ws) -> int:
    last = HEADER_ROW
    for r in range(DATA_START, (ws.max_row or DATA_START) + 1):
        if _s(_cell(ws, r, "A")) or _s(_cell(ws, r, "J")):
            last = r
    return last


def run(db, batch: ImportBatch, wb, apply: bool, default_nspt: str = "") -> None:
    ws = next((w for w in wb.worksheets if w.title.strip().startswith("6.")), None)
    counts = {"created": 0, "updated": 0, "skipped": 0, "warning": 0, "review": 0, "error": 0}
    logs: list[dict] = []
    changes: list[dict] = []
    uid = batch.created_by

    def log(row_no, level, category, message, ref_key="", target_code=""):
        logs.append({"sheet": "6.PO", "row_no": row_no, "level": int(level), "category": category,
                     "message": message, "ref_key": ref_key, "target_code": target_code})
        if level == LogLevel.WARNING:
            counts["warning"] += 1
        elif level == LogLevel.REVIEW:
            counts["review"] += 1
        elif level == LogLevel.ERROR:
            counts["error"] += 1

    if ws is None:
        log(0, LogLevel.WARNING, "missing_sheet", "Không thấy sheet '6. TIẾN ĐỘ MUA HÀNG'")
        db.rollback()
        _persist(db, batch, counts, logs, [], 0)
        return

    ig_map = {_ncode(g.name): g.name for g in db.query(ItemGroup).all()}
    unit_map = {_ncode(u.name): u.name for u in db.query(Unit).all()}
    wh_map: dict = {}
    for w in db.query(Warehouse).all():
        wh_map[_ncode(w.code)] = w.code
        wh_map[_ncode(w.name)] = w.code
    comp_map: dict = {}
    for c in db.query(Company).all():
        comp_map[_ncode(c.code)] = c.id
        comp_map[_ncode(c.name)] = c.id
        if (c.tax_code or "").strip():
            comp_map[_ncode(c.tax_code)] = c.id
    prod_codes = {_ncode(p.code) for p in db.query(Product).all() if (p.code or "").strip()}
    _seen_unmatched: set = set()

    def cat(value, cmap, label, r):
        v = _s(value)
        if not v:
            return ""
        canon = cmap.get(_ncode(v))
        if canon:
            return canon
        key = (label, _ncode(v))
        if key not in _seen_unmatched:
            _seen_unmatched.add(key)
            log(r, LogLevel.REVIEW, "value_unmatched", f"{label} '{v}' không có trong danh mục — giữ text", ref_key=v)
        return v

    def canon_supplier(raw):
        raw = _s(raw)
        if not raw:
            return ""
        s = (db.query(Supplier).filter(Supplier.code == raw).first()
             or db.query(Supplier).filter(Supplier.tax_code == raw).first())
        return s.code if s else raw

    def resolve_company(raw, r):
        v = _s(raw)
        if not v:
            return 0
        cid = comp_map.get(_ncode(v))
        if cid:
            return cid
        key = ("Công ty", _ncode(v))
        if key not in _seen_unmatched:
            _seen_unmatched.add(key)
            log(r, LogLevel.REVIEW, "value_unmatched", f"Pháp lý '{v}' không khớp Công ty — để trống", ref_key=v)
        return 0

    def resolve_wh(raw, r):
        v = _s(raw)
        if not v:
            return ""
        return cat(v, wh_map, "Kho", r)

    def ensure_product(code, name, unit, ig, r):
        if not code:
            return
        if _ncode(code) in prod_codes:
            return
        db.add(Product(code=code, name=name or code, item_group=ig, unit=unit,
                       is_active=True, created_by=uid, updated_by=uid))
        db.flush()
        prod_codes.add(_ncode(code))
        log(r, LogLevel.INFO, "product_created", f"Tạo SP tối thiểu '{code}' từ đơn", ref_key=code)

    # ---- đọc & gom dòng ----
    def row_data(r):
        return {
            "misa": _scode(_cell(ws, r, "J")), "order_date": _d(_cell(ws, r, "AD")),
            "company": _s(_cell(ws, r, "G")), "department": _s(_cell(ws, r, "F")),
            "supplier": canon_supplier(_cell(ws, r, "I")), "nspt": _s(_cell(ws, r, "H")) or default_nspt,
            "payment_terms": _s(_cell(ws, r, "AT")),
            "product_code": _scode(_cell(ws, r, "L")), "product_name": _s(_cell(ws, r, "M")),
            "invoice_no": _scode(_cell(ws, r, "AE")), "invoice_name": _s(_cell(ws, r, "O")),
            "item_group": cat(_cell(ws, r, "K"), ig_map, "Phân loại", r), "spec": _s(_cell(ws, r, "N")),
            "unit": cat(_cell(ws, r, "W"), unit_map, "ĐVT", r), "qty_request": _n(_cell(ws, r, "V")),
            "qty_order": _n(_cell(ws, r, "X")), "price": _n(_cell(ws, r, "Z")), "vat": _vat(_cell(ws, r, "AA")),
            "warehouse": resolve_wh(_cell(ws, r, "R"), r), "supplier_ready": _b(_cell(ws, r, "Q")),
            "required_date": _d(_cell(ws, r, "C")), "progress": _s(_cell(ws, r, "P")),
            "fg_code": _scode(_cell(ws, r, "AP")), "fg_name": _s(_cell(ws, r, "AR")), "note": _s(_cell(ws, r, "AC")),
            # delivery
            "carrier": canon_supplier(_cell(ws, r, "S")), "ship_qty": _n(_cell(ws, r, "T")),
            "ship_unit": cat(_cell(ws, r, "U"), unit_map, "ĐVT", r), "received_qty": _n(_cell(ws, r, "Y")),
            "received_date": _d(_cell(ws, r, "E")), "promised_date": _d(_cell(ws, r, "D")),
            "ship_price": _n(_cell(ws, r, "AJ")), "ship_amount": _n(_cell(ws, r, "AK")),
            "progress_note": _s(_cell(ws, r, "AG")), "company_id": resolve_company(_cell(ws, r, "G"), r),
        }

    last = _last_row(ws)
    total_rows = 0
    misa_order: list = []
    by_misa: dict = {}
    for r in range(DATA_START, last + 1):
        misa = _s(_cell(ws, r, "J"))
        if not misa:
            if _s(_cell(ws, r, "A")):
                log(r, LogLevel.ERROR, "missing_key", "Thiếu Mã Misa"); counts["skipped"] += 1
            continue
        total_rows += 1
        d = row_data(r)
        if misa not in by_misa:
            by_misa[misa] = []; misa_order.append(misa)
        by_misa[misa].append((r, d))
    batch.sheet_info = json.dumps({"rows": total_rows, "orders": len(misa_order)}, ensure_ascii=False)

    seen_delivery: set = set()

    def po_snapshot(po: PurchaseOrder) -> str:
        def cols(o):
            return {c.key: getattr(o, c.key) for c in sa_inspect(o).mapper.column_attrs
                    if c.key not in ("created_at", "updated_at")}
        items = po_service.items_of(db, po.id)
        data = {"po": cols(po), "items": []}
        for it in items:
            row = cols(it)
            row["_deliveries"] = [cols(x) for x in po_service.deliveries_of(db, it.id)]
            data["items"].append(row)
        return json.dumps(data, ensure_ascii=False, default=str)

    def upsert_po(misa, d) -> tuple:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.misa_code == misa).first()
        was_new = po is None
        sup = db.query(Supplier).filter(Supplier.code == d["supplier"]).first()
        fields = dict(misa_code=misa, supplier_code=d["supplier"],
                      supplier_name=(sup.name if sup else d["supplier"]), company_id=d["company_id"],
                      department=d["department"], nspt=d["nspt"], order_date=d["order_date"],
                      payment_terms=d["payment_terms"])
        if po is None:
            po = PurchaseOrder(status="approved", created_by=uid, updated_by=uid, **fields)
            db.add(po); db.flush(); po.code = f"PO{po.id:05d}"
            log(0, LogLevel.INFO, "po_new", f"Tạo đơn mới {po.code} (Misa {misa})", ref_key=misa, target_code=po.code)
        else:
            for k, v in fields.items():
                setattr(po, k, v)
            po.updated_by = uid
            log(0, LogLevel.INFO, "po_update", f"Cập nhật đơn {po.code} (Misa {misa})", ref_key=misa, target_code=po.code)
        return po, was_new

    def upsert_item(po, d):
        it = db.query(POItem).filter(POItem.po_id == po.id, POItem.product_code == d["product_code"],
                                     POItem.invoice_no == d["invoice_no"]).first()
        fields = dict(product_code=d["product_code"], product_name=d["product_name"], invoice_name=d["invoice_name"],
                      item_group=d["item_group"], spec=d["spec"], fg_code=d["fg_code"], fg_name=d["fg_name"],
                      invoice_no=d["invoice_no"], supplier_ready=d["supplier_ready"], required_date=d["required_date"],
                      unit=d["unit"], qty_request=d["qty_request"], qty_order=d["qty_order"], price=d["price"],
                      vat=d["vat"], warehouse_code=d["warehouse"], note=d["note"][:255],
                      progress_status=_PROGRESS.get(_ncode(d["progress"]).lower(), d["progress"] or "Chưa đặt hàng"))
        fields, _t = _fit(POItem, fields)
        if it is None:
            it = POItem(po_id=po.id, created_by=uid, updated_by=uid, **fields)
            db.add(it); db.flush()
        else:
            for k, v in fields.items():
                setattr(it, k, v)
        return it

    def upsert_delivery(po, it, d, r):
        # Khoá lần giao = HĐ + ngày nhận + KHO + VẬN CHUYỂN. Cùng HĐ vẫn có thể giao
        # nhiều lần (khác kho / khác đơn vị VC) -> là các lần giao riêng, KHÔNG phải trùng.
        dk = (it.id, d["invoice_no"], d["received_date"], d["warehouse"], d["carrier"])
        dup = dk in seen_delivery
        seen_delivery.add(dk)
        dv = db.query(PODelivery).filter(PODelivery.po_item_id == it.id,
                                         PODelivery.invoice_no == d["invoice_no"],
                                         PODelivery.received_date == d["received_date"],
                                         PODelivery.warehouse_code == d["warehouse"],
                                         PODelivery.carrier_code == d["carrier"]).first()
        fields = dict(po_id=po.id, warehouse_code=d["warehouse"], carrier_code=d["carrier"],
                      carrier_name=(d["carrier"] or ""), ship_qty=d["ship_qty"], ship_unit=d["ship_unit"],
                      received_qty=d["received_qty"], received_date=d["received_date"],
                      promised_date=d["promised_date"], invoice_no=d["invoice_no"],
                      shipping_unit_price=d["ship_price"], shipping_amount=d["ship_amount"],
                      progress_note=d["progress_note"])
        fields, _t = _fit(PODelivery, fields)
        if dv is None:
            dv = PODelivery(po_item_id=it.id, created_by=uid, updated_by=uid, **fields)
            db.add(dv); db.flush(); counts["created"] += 1
        else:
            for k, v in fields.items():
                setattr(dv, k, v)
            counts["updated"] += 1
            if dup:
                log(r, LogLevel.WARNING, "duplicate_line",
                    f"Lần giao trùng (Misa {po.misa_code} + SP {it.product_code} + HĐ {d['invoice_no']} + ngày {d['received_date']} + kho {d['warehouse']} + VC {d['carrier']}) — ghi đè", ref_key=it.product_code, target_code=po.code)

    # ---- xử lý từng Misa ----
    for misa in misa_order:
        grp = by_misa[misa]
        po, was_new = upsert_po(misa, grp[0][1])
        snap = "" if was_new else po_snapshot(po)   # chụp TRƯỚC khi sửa dòng
        # gom theo (product + invoice)
        item_order: list = []
        item_rows: dict = {}
        for r, d in grp:
            k = (d["product_code"], d["invoice_no"])
            if k not in item_rows:
                item_rows[k] = []; item_order.append(k)
            item_rows[k].append((r, d))
        done_items: list = []
        for k in item_order:
            irows = item_rows[k]
            r0, d0 = irows[0]
            ensure_product(d0["product_code"], d0["product_name"], d0["unit"], d0["item_group"], r0)
            it = upsert_item(po, d0)
            xs = {round(_n(x["qty_order"]), 3) for _, x in irows}
            if len(xs) > 1:
                log(r0, LogLevel.REVIEW, "qty_order_mismatch",
                    f"SL đặt lệch giữa các lần giao ({sorted(xs)}) — lấy dòng đầu, cần rà", ref_key=d0["product_code"], target_code=po.code)
            for r, d in irows:
                upsert_delivery(po, it, d, r)
            db.flush()
            if it.progress_status == "Hoàn thành":
                done_items.append(it)
        db.flush()
        po_service.recompute_effects(db, po, uid)
        _auto_pay(db, po, done_items, apply, uid, log, counts)
        # Tự tiến trạng thái dòng theo thực tế (nhận/số HĐ/đã trả) — forward-only, không hạ cấp.
        # Dòng đã auto-pay đã được set_status đẩy lên 'Hoàn thành'; các dòng còn lại tiến tới bước đạt được.
        for it in po_service.items_of(db, po.id):
            po_service.auto_advance_line(db, po, it)
        changes.append({"survey_id": po.id, "was_new": was_new, "snapshot": snap})

    if apply:
        db.commit()
    else:
        db.rollback()
    _persist(db, batch, counts, logs, changes if apply else [], total_rows)


def _auto_pay(db, po, done_items, apply, uid, log, counts):
    """Dòng 'Hoàn thành' -> tạo YCTT + ghi ĐÃ CHI (chỉ khi Ghi). Dry-run chỉ đếm + log."""
    if not done_items:
        return
    payable_ids = []
    for it in done_items:
        for d in po_service.deliveries_of(db, it.id):
            p = (db.query(Payable)
                 .filter(Payable.source_type == "goods", Payable.ref_type == "delivery", Payable.ref_id == d.id)
                 .first())
            if p and float(p.remaining or 0) > 0:
                payable_ids.append(p.id)
    if not payable_ids:
        return
    if not apply:
        log(0, LogLevel.INFO, "autopay_preview",
            f"[Chạy thử] Sẽ tạo YCTT + ghi ĐÃ CHI cho {len(payable_ids)} khoản nợ (đơn {po.code})", target_code=po.code)
        return
    reqs = pr_service.create_requests(
        db, PRequestCreate(request_date=po.order_date or "", note=f"Import Misa {po.misa_code}",
                           lines=[LineIn(payable_id=pid, amount=0) for pid in payable_ids]), uid)
    for req in reqs:
        pr_service.set_status(db, req.id, "paid", uid)
    log(0, LogLevel.INFO, "autopay",
        f"Đã tạo {len(reqs)} YCTT + ghi ĐÃ CHI {len(payable_ids)} khoản (đơn {po.code})", target_code=po.code)
