"""Dựng kết quả API của Đơn mua hàng (bao-CR-711: dời nguyên từ `controller.py`, không đổi hành vi).

`_out` là bản ĐẦY ĐỦ của một đơn (màn chi tiết, bản in, Yêu cầu thanh toán đọc chung một con số);
`_out_list` / `_out_lines` là hai màn danh sách; `_out_print` thêm khối pháp nhân · NCC · kho của
bản in. Truy vấn nằm ở `service.py`; thứ tự khóa trong từng dict giữ như bản cũ.
"""
from sqlalchemy.orm import Session

from app.core.status_codes import (PO_DELIVERY_STATUS, PO_DOCUMENT_STATUS,
                                   PO_ITEM_LINE_STATUS, PO_PROGRESS_STATUS)
from app.modules.payable.model import Payable

from . import service
from .model import (ALLOCATION_METHOD_LABELS, AllocationMethod, COST_STAGE_LABELS,
                    COST_STAGE_PREFIX, CostStage, DEFAULT_CURRENCY, ORDER_TYPE_LABELS, OrderType,
                    POItem, PurchaseOrder)

HEADER = ["id", "code", "misa_code", "pr_code", "survey_code", "company_id", "supplier_code",
          "supplier_name", "department_id", "handler_dept_id", "department", "nspt_id", "nspt",
          "order_date", "vat_rate", "payment_terms",
          "is_urgent", "status", "document_status", "note", "approve_note",
          "order_type", "currency", "customs_decl_no", "customs_decl_date", "etd_date",
          "inspection_days", "return_days", "invoice_deadline", "cost_stage"]


def _delivery(d, pay=None) -> dict:
    return {"id": d.id, "delivery_no": d.delivery_no, "warehouse_code": d.warehouse_code,
            "carrier_code": d.carrier_code, "carrier_name": d.carrier_name,
            "ship_qty": float(d.ship_qty or 0), "ship_unit": d.ship_unit,
            "received_qty": float(d.received_qty or 0), "promised_date": d.promised_date,
            "expected_date": d.expected_date, "received_date": d.received_date,
            "std_days": d.std_days, "regulated_date": d.regulated_date,
            "diff_promise": d.diff_promise, "diff_regulated": d.diff_regulated, "diff_required": d.diff_required,
            "invoice_no": d.invoice_no, "invoice_date": getattr(d, "invoice_date", "") or "",
            "shipping_unit_price": float(d.shipping_unit_price or 0),
            "shipping_amount": float(d.shipping_amount or 0), "qc_result": d.qc_result,
            # MÃ (B-06) + nhãn gửi kèm, xem chú thích ở `_item` bên dưới.
            "status": d.status, "status_label": PO_DELIVERY_STATUS.label_of(d.status),
            "extra_request": d.extra_request, "progress_note": d.progress_note,
            # Công nợ HÀNG của lần giao này (đã trả / còn lại)
            "goods_total": float(pay.total or 0) if pay else 0.0,
            "paid": float(pay.paid_amount or 0) if pay else 0.0,
            "remaining": float(pay.remaining or 0) if pay else 0.0}


def _item(db, it, pay_by_del: dict, inv_by_code: dict | None = None,
          pr_expected: dict | None = None) -> dict:
    dels = service.deliveries_of(db, it.id)
    qty_order = float(it.qty_order or 0)
    del_out = [_delivery(d, pay_by_del.get(d.id)) for d in dels]
    # Tên trên hóa đơn: ưu tiên giá trị lưu trên DÒNG; nếu dòng trống (phiếu tạo trước khi có
    # field / copy từ YCMH) thì suy từ SẢN PHẨM master theo product_code để modal + phiếu in
    # hiện đúng "tên trên hóa đơn" thay vì rơi về tên hàng hóa.
    inv_name = (it.invoice_name or "").strip() or (inv_by_code or {}).get((it.product_code or "").strip(), "")
    return {"id": it.id, "product_code": it.product_code, "product_name": it.product_name,
            "invoice_name": inv_name, "item_group": it.item_group, "spec": it.spec,
            "fg_code": it.fg_code, "fg_name": it.fg_name, "invoice_no": it.invoice_no,
            "invoice_date": it.invoice_date or "",
            "document_delivery_date": it.document_delivery_date or "",
            "supplier_ready": bool(it.supplier_ready), "required_date": it.required_date,
            "expected_date": it.expected_date or "",
            # Ngày dự kiến ĐANG ghi trên dòng YCMH nguồn — CHỈ ĐỂ ĐỌC. FE so với ô bên trên để
            # bật popup cảnh báo lệch ngày; hệ thống không tự ghi ngược lên YCMH (CR-062).
            "pr_expected_date": (pr_expected or {}).get((it.product_code or "").strip(), ""),
            "unit": it.unit, "qty_request": float(it.qty_request or 0), "qty_order": qty_order,
            "price": float(it.price or 0), "vat": float(it.vat or 0), "amount": float(it.amount or 0),
            # bao-CR-319: `price` / `amount` / `order_total` là NGUYÊN TỆ theo `currency` của dòng;
            # `base_amount` và các số công nợ bên dưới (goods/paid/remaining) là bản QUY ĐỔI.
            "currency": it.currency or "", "exchange_rate": service.rate_of(it),
            "base_amount": float(it.base_amount or 0) or float(it.amount or 0),
            "weight_kg": float(it.weight_kg or 0), "dimension": it.dimension or "",
            "qty_received": float(it.qty_received or 0), "qty_remaining": float(it.qty_remaining or 0),
            # `line_status` / `progress_status` là MÃ (B-06); `*_label` là chữ để hiện.
            # Giao diện đừng tự dịch mã sang tiếng Việt — dùng nhãn gửi kèm.
            "line_status": it.line_status,
            "line_status_label": PO_ITEM_LINE_STATUS.label_of(it.line_status),
            "warehouse_code": it.warehouse_code, "note": it.note,
            "progress_status": it.progress_status or service.PROG_NOT_ORDERED,
            "progress_status_label": PO_PROGRESS_STATUS.label_of(
                it.progress_status or service.PROG_NOT_ORDERED),
            "pause_reason": it.pause_reason or "", "status_before_pause": it.status_before_pause or "",
            "status_before_pause_label": PO_PROGRESS_STATUS.label_of(it.status_before_pause or ""),
            # Giao thiếu: tổng SL đã nhận < SL đặt (dùng cho badge cảnh báo ở FE)
            "is_short_delivery": bool(qty_order > 0 and float(it.qty_received or 0) + 0.001 < qty_order),
            # Tiền theo DÒNG: đặt hàng (SL đặt) · tiền hàng đã nhận (có công nợ) · đã trả · còn lại
            "order_total": round(qty_order * float(it.price or 0) * (1 + float(it.vat or 0) / 100), 2),
            "goods_total": round(sum(x["goods_total"] for x in del_out), 2),
            "paid_total": round(sum(x["paid"] for x in del_out), 2),
            "remaining_total": round(sum(x["remaining"] for x in del_out), 2),
            "deliveries": del_out}


def _stage_label(stage) -> str:
    return COST_STAGE_LABELS.get(service.stage_of(stage), "")


def _import_cost(c, pay: Payable | None, po: PurchaseOrder, types: dict | None = None) -> dict:
    """Một dòng CHI PHÍ THU MUA — trả cả SỐ lẫn NHÃN (R2/QĐ-11), ba giai đoạn (bao-CR-453).

    Mỗi giai đoạn ba số: `<gđ>_amount` nguyên tệ trước thuế · `<gđ>_rate` tỷ giá riêng ·
    `<gđ>_base` đã gồm VAT và quy đổi (None = giai đoạn chưa có số). `effective_base` là số
    đang có hiệu lực của dòng; `base_amount` GIỮ tên cũ và bằng đúng số đó để bản in / màn
    cũ / phép chia không phải đổi. Chênh lệch `variance_*` = Quyết toán − Dự toán, chỉ có
    khi dòng đã ở Quyết toán và có số Dự toán.

    `pay` là khoản nợ của dòng (bao-CR-319 P5), None khi dòng chưa Quyết toán / đơn chưa duyệt:
    khi đó `payable_id = 0`, đã chi 0 và còn lại = số hiệu lực để giao diện vẫn cộng được.
    """
    try:
        alloc = AllocationMethod(int(c.allocation_method or 0))
    except ValueError:
        alloc = AllocationMethod.BY_VALUE
    effective_stage = service.effective_stage_of(c, po)
    effective_base = service.effective_base_of(c, po)
    paid = float(pay.paid_amount or 0) if pay else 0.0
    d = {"id": c.id, "cost_type": int(c.cost_type or 0),
         "cost_type_name": service.cost_type_name(c.cost_type, types),
         "creates_payable": service.cost_type_creates_payable(c.cost_type, types),
         "line_stage": int(service.stage_of(c.line_stage)),
         "effective_stage": int(effective_stage),
         "effective_stage_label": COST_STAGE_LABELS.get(effective_stage, ""),
         "payable_id": pay.id if pay else 0,
         "paid_amount": round(paid, 2),
         "remaining": round(float(pay.remaining or 0), 2) if pay else round(effective_base, 2),
         "payable_status": (pay.status or "") if pay else "",
         "description": c.description or "",
         "supplier_code": c.supplier_code or "", "supplier_name": c.supplier_name or "",
         "currency": c.currency or DEFAULT_CURRENCY, "vat": float(c.vat or 0),
         "effective_base": effective_base, "base_amount": effective_base,
         #  Số NGUYÊN TỆ của giai đoạn hiệu lực — bản in đơn nhập khẩu v1 in cột này kèm mã tiền
         #  (trước đây đọc `amount`, cột đã bỏ ở bao-CR-453 nên lùi về số VNĐ mà vẫn ghi USD).
         "effective_amount": service.cost_amount_of(c, effective_stage),
         "allocation_method": int(alloc),
         "allocation_method_label": ALLOCATION_METHOD_LABELS.get(alloc, ""),
         "allocation_target": c.allocation_target or "",
         "manual_allocation": service.parse_manual_allocation(getattr(c, "manual_allocation", "")),
         "invoice_no": c.invoice_no or "", "invoice_date": c.invoice_date or "",
         "payment_due_date": c.payment_due_date or "", "note": c.note or ""}
    # Nhãn cũ giữ cho màn v1/v2 chưa port đọc được: `cost_type_label` = tên trong danh mục.
    d["cost_type_label"] = d["cost_type_name"]
    for stage, prefix in COST_STAGE_PREFIX.items():
        d[f"{prefix}_amount"] = service.cost_amount_of(c, stage)
        d[f"{prefix}_rate"] = service.cost_rate_of(c, stage)
        d[f"{prefix}_base"] = service.cost_base_of(c, stage)
    est, fin = d["estimate_base"], d["final_base"]
    if effective_stage == CostStage.FINAL and est is not None and fin is not None:
        d["variance_base"] = round(fin - est, 2)
        d["variance_pct"] = round((fin - est) / est * 100, 2) if est else None
    else:
        d["variance_base"] = None
        d["variance_pct"] = None
    return d


def _import_cost_summary(rows: list[dict], goods_base: float, shipping_total: float,
                         po_stage) -> dict:
    """Cụm tổng CHI PHÍ THU MUA của đơn — gom theo LOẠI và theo NHÀ CUNG CẤP.

    Gom sẵn ở backend vì P5 tạo Yêu cầu thanh toán gom theo NCC từ đúng con số này;
    để giao diện tự cộng thì hai nơi dễ lệch nhau. Mọi số ở đây đã quy đổi về VNĐ.

    bao-CR-453: `cost_total` = tổng số HIỆU LỰC của mọi dòng (mỗi dòng theo giai đoạn cao nhất
    đã điền); ba tổng theo giai đoạn chỉ cộng dòng CÓ số ở giai đoạn đó. Đã chi / còn lại
    chỉ đếm dòng đã Quyết toán vì chỉ dòng đó mới có công nợ.
    """
    cost_total = round(sum(r["effective_base"] for r in rows), 2)
    final_rows = service.final_costs(rows)
    paid_total = round(sum(r["paid_amount"] for r in final_rows), 2)
    final_remaining = round(sum(r["remaining"] for r in final_rows), 2)
    stage_totals = {prefix: round(sum(r[f"{prefix}_base"] for r in rows
                                      if r.get(f"{prefix}_base") is not None), 2)
                    for prefix in COST_STAGE_PREFIX.values()}
    compared = [r for r in rows if r.get("variance_base") is not None]
    variance_total = round(sum(r["variance_base"] for r in compared), 2)
    compared_estimate = round(sum(r["estimate_base"] for r in compared), 2)
    by_type: dict[int, dict] = {}
    by_supplier: dict[str, dict] = {}
    for r in rows:
        g = by_type.setdefault(r["cost_type"], {"cost_type": r["cost_type"],
                                                "cost_type_label": r["cost_type_label"],
                                                "base_amount": 0.0, "count": 0})
        g["base_amount"] = round(g["base_amount"] + r["effective_base"], 2)
        g["count"] += 1
        code = r["supplier_code"] or ""
        # P5: mỗi NCC một dòng tổng · đã chi · còn lại + danh sách id khoản nợ CÒN NỢ để nút
        # "Tạo yêu cầu thanh toán" của NCC đó đưa thẳng sang màn lập phiếu (mỗi phiếu một NCC).
        n = by_supplier.setdefault(code, {"supplier_code": code, "supplier_name": r["supplier_name"],
                                          "base_amount": 0.0, "paid_amount": 0.0, "remaining": 0.0,
                                          "count": 0, "unpaid_payable_ids": []})
        n["base_amount"] = round(n["base_amount"] + r["effective_base"], 2)
        n["count"] += 1
        if not n["supplier_name"]:
            n["supplier_name"] = r["supplier_name"]
        if int(r.get("effective_stage") or 0) == int(CostStage.FINAL):
            n["paid_amount"] = round(n["paid_amount"] + r["paid_amount"], 2)
            n["remaining"] = round(n["remaining"] + r["remaining"], 2)
            if r["payable_id"] and r["remaining"] > 0.01:
                n["unpaid_payable_ids"].append(r["payable_id"])
    stage = service.stage_of(po_stage)
    return {
        "goods_base_total": round(goods_base, 2),          # tiền HÀNG đã quy đổi (theo SL đặt)
        "cost_total": cost_total,                          # tổng chi phí HIỆU LỰC đã quy đổi
        "effective_total": cost_total,
        "estimate_total": stage_totals["estimate"],
        "provisional_total": stage_totals["provisional"],
        "final_total": stage_totals["final"],
        "variance_total": variance_total,                  # Quyết toán − Dự toán (dòng so được)
        "variance_pct": (round(variance_total / compared_estimate * 100, 2)
                         if compared_estimate else None),
        "shipping_total": round(shipping_total, 2),        # cước trên lần giao — CHỈ XEM, không cộng
        "paid_total": paid_total,                          # đã chi cho chi phí (P5), dòng Quyết toán
        "remaining_total": final_remaining,                # còn phải chi (P5), dòng Quyết toán
        "landed_total": round(goods_base + cost_total, 2),  # tổng giá vốn lô hàng về tới kho
        "stage": int(stage),
        "stage_label": COST_STAGE_LABELS.get(stage, ""),
        "lines_not_final": len(rows) - len(final_rows),
        "lines_without_supplier": sum(1 for r in rows if r["creates_payable"] and not r["supplier_code"]),
        "by_type": sorted(by_type.values(), key=lambda x: -x["base_amount"]),
        "by_supplier": sorted(by_supplier.values(), key=lambda x: -x["base_amount"]),
    }


def _out(db: Session, po: PurchaseOrder) -> dict:
    d = {c: getattr(po, c) for c in HEADER}
    d["vat_rate"] = float(po.vat_rate or 0)
    # bao-CR-480: màn ĐMH từ nay hiện "Phòng xử lý" — trước chỉ có id trần, hai bản giao diện
    # đều không bày, nên mở một đơn nhà máy mua hộ phòng khác không có gì báo ai đang mua.
    from app.modules.purchase_request.service import handler_dept_name_of
    d["handler_dept_name"] = handler_dept_name_of(db, po.handler_dept_id)
    # bao-CR-524: đơn cũ còn `0` hiện đúng id phòng thu mua mặc định.
    from app.core.central_purchasing import normalize_handler_dept_id
    d["handler_dept_id"] = normalize_handler_dept_id(db, po.handler_dept_id)
    # bao-CR-490: trưởng phòng phê duyệt (người thực bấm Duyệt) + trưởng phòng theo hồ sơ.
    from app.core.print_signers import approver_fields
    d.update(approver_fields(db, po))
    # `document_status` là MÃ (B-06) — trước đây nó là chữ tiếng Việt VIẾT THƯỜNG nên mỗi màn
    # lại tự viết hoa một kiểu ("Đã có chứng từ" ở ô lọc, "đã có thông tin chứng từ" ở bảng).
    d["document_status_label"] = PO_DOCUMENT_STATUS.label_of(po.document_status)
    # bao-CR-319 — loại đơn: trả cả SỐ lẫn NHÃN, tiếng Việt chỉ nằm ở tầng hiển thị (R2/QĐ-11)
    d["order_type"] = int(po.order_type or OrderType.DOMESTIC)
    d["order_type_label"] = ORDER_TYPE_LABELS.get(OrderType(d["order_type"]), "")
    d["currency"] = po.currency or DEFAULT_CURRENCY
    d["exchange_rate"] = service.rate_of(po)
    # Công nợ theo lần giao: HÀNG (goods) hiện đã trả/còn lại trên dòng; gom cả VẬN CHUYỂN cho tổng chưa trả
    all_pays = service.delivery_payables_of(db, po.id)
    pay_by_del = {p.ref_id: p for p in all_pays if p.source_type == "goods"}
    it_list = service.items_of(db, po.id)
    # Nạp sẵn "tên trên hóa đơn" từ sản phẩm master cho các dòng đang trống (tránh N+1)
    need_codes = {(it.product_code or "").strip() for it in it_list
                  if not (it.invoice_name or "").strip() and (it.product_code or "").strip()}
    inv_by_code = service.invoice_names_by_code(db, need_codes)
    pr_expected = service.pr_expected_map(db, po.pr_code)
    items = [_item(db, it, pay_by_del, inv_by_code, pr_expected) for it in it_list]
    d["items"] = items
    # Tổng theo SL THỰC NHẬN (thành tiền đơn hàng = đã chốt)
    subtotal = round(sum(i["qty_received"] * i["price"] for i in items), 2)
    vat = round(sum(i["amount"] - i["qty_received"] * i["price"] for i in items), 2)
    shipping = round(sum(dl["shipping_amount"] for i in items for dl in i["deliveries"]), 2)
    d["subtotal"] = subtotal
    d["vat"] = vat
    d["total"] = round(subtotal + vat, 2)
    d["shipping_total"] = shipping
    # Tổng theo SL ĐẶT (cho bản in đặt hàng gửi NCC)
    order_sub = round(sum(i["qty_order"] * i["price"] for i in items), 2)
    order_vat = round(sum(i["qty_order"] * i["price"] * (i["vat"] / 100) for i in items), 2)
    d["order_subtotal"] = order_sub
    d["order_total"] = round(order_sub + order_vat, 2)
    # bao-CR-319 P3 / bao-CR-453 — CHI PHÍ THU MUA của đơn (mọi loại đơn), ba giai đoạn.
    # Khóa API giữ tên lịch sử `import_costs` để màn cũ đọc được; nhãn hiển thị đã đổi.
    cost_pays = service.import_cost_payables_of(db, po.id)
    cost_types = service.cost_type_map(db)
    costs = [_import_cost(c, cost_pays.get(c.id), po, cost_types)
             for c in service.import_costs_of(db, po.id)]
    # Tổng công nợ CHƯA TRẢ (hàng + vận chuyển + chi phí thu mua) → dùng bật nút Tạo yêu cầu thanh toán
    d["unpaid_total"] = round(sum(float(p.remaining or 0) for p in all_pays)
                              + sum(float(p.remaining or 0) for p in cost_pays.values()), 2)
    d["import_costs"] = costs
    d["cost_stage"] = int(service.stage_of(po.cost_stage))
    d["cost_stage_label"] = _stage_label(po.cost_stage)
    goods_base = round(sum(i["order_total"] * i["exchange_rate"] for i in items), 2)
    d["import_cost_summary"] = _import_cost_summary(costs, goods_base, shipping, po.cost_stage)
    # bao-CR-319 P4 — chi phí chia về từng dòng hàng, CHỈ ĐỂ XEM (không lưu, không vào kho).
    # Tính ở đây để màn hình, bản in và Yêu cầu thanh toán (P5) đọc cùng một con số.
    # bao-CR-453: một bản chia cho MỖI giai đoạn + bản "effective" theo số hiệu lực từng dòng.
    allocation = {str(int(stage)): service.allocate_import_costs(items, costs, stage)
                  for stage in CostStage}
    allocation["effective"] = service.allocate_import_costs(items, costs)
    d["import_cost_allocation"] = allocation
    return d


def _out_list(db: Session, items: list) -> list[dict]:
    """Các dòng của màn danh sách ĐMH — tiền hàng, mã YCMH, tên hiển thị gom cả trang một lượt."""
    amounts = service.order_amount_map(db, [p.id for p in items])
    out = []
    for p in items:
        row = {c: getattr(p, c) for c in HEADER}
        row["created_at"] = p.created_at   # thời điểm tạo (có giờ) — hiển thị giờ VN ở list
        row["updated_at"] = p.updated_at   # bao-CR-294 — cột "Ngày cập nhật" + sort ở màn danh sách
        # Tiền hàng ở danh sách = GIÁ TRỊ ĐẶT HÀNG (SL đặt × đơn giá × VAT) — ổn định, không về 0
        # khi dòng chuyển sang `ordered` mà chưa nhận (it.amount tính theo SL thực nhận).
        # bao-CR-319: cột này đứng chung một bảng với đơn trong nước nên phải là số ĐÃ QUY ĐỔI
        # (đơn VNĐ có tỷ giá 1 → không đổi số cũ). Không quy đổi thì đơn ngoại tệ nằm cạnh đơn
        # nội tệ mà không cách nào biết cột nào là tiền gì.
        # bao-CR-436: gom cả trang một lượt truy vấn — luật tính nằm trong `order_amount_map`.
        row["amount"] = amounts.get(p.id, 0.0)
        row["order_type"] = int(p.order_type or OrderType.DOMESTIC)
        row["order_type_label"] = ORDER_TYPE_LABELS.get(OrderType(row["order_type"]), "")
        out.append(row)
    # Gắn pr_id (id phiếu YCMH theo mã PYC) để FE điều hướng sang chi tiết PYC khi click Mã PYC
    codes = {r["pr_code"] for r in out if r.get("pr_code")}
    if codes:
        id_by_code = service.pr_ids_by_code(db, codes)
        for r in out:
            r["pr_id"] = id_by_code.get(r.get("pr_code"))
    # bao-CR-705: Phòng xử lý, Trưởng phòng phê duyệt + các cột ẩn sẵn (công ty, người tạo, tỷ giá)
    extra = service.list_display_names(db, items)
    for r in out:
        r.update(extra.get(r["id"], {}))
    return out


def _out_lines(rows, recv: dict, wh: str) -> list[dict]:
    """Màn DÒNG HÀNG theo kho (trang chi tiết Kho). `recv` = `{id dòng: (nhận tại kho này,
    nhận đã gắn kho bất kỳ)}` từ `service.received_by_warehouse`."""
    def _recv_here(it: POItem) -> float:
        here, assigned = recv.get(it.id, (0.0, 0.0))
        if it.warehouse_code == wh:   # phần đã nhận chưa gắn lần giao/kho nào → về kho mặc định
            here += max(0.0, float(it.qty_received or 0) - assigned)
        return round(here, 3)

    return [{
        "po_id": po.id, "po_code": po.code, "order_date": po.order_date, "po_status": po.status,
        "supplier_code": po.supplier_code, "supplier_name": po.supplier_name,
        "item_id": it.id, "product_code": it.product_code, "product_name": it.product_name,
        "unit": it.unit, "required_date": it.required_date, "warehouse_code": it.warehouse_code,
        "qty_order": float(it.qty_order or 0), "qty_received": float(it.qty_received or 0),
        "qty_remaining": float(it.qty_remaining or 0),
        "qty_received_here": _recv_here(it) if wh else 0.0,
        "line_status": it.line_status,
        "line_status_label": PO_ITEM_LINE_STATUS.label_of(it.line_status),
        "progress_status": it.progress_status or service.PROG_NOT_ORDERED,
        "progress_status_label": PO_PROGRESS_STATUS.label_of(
            it.progress_status or service.PROG_NOT_ORDERED),
    } for po, it in rows]


# Đơn đã qua duyệt thì mới in chữ ký người duyệt. Hủy duyệt (CR-108) đưa đơn về `draft`
# nên nó tự rơi khỏi tập này; đơn bị hủy / từ chối cũng không in chữ ký duyệt.
_PO_APPROVED_STATUSES = {"approved", "partial", "received", "completed"}


def resolve_print_signers(db: Session, po: PurchaseOrder) -> dict:
    """Họ tên + ảnh chữ ký cho các ô ký trên bản in Đơn mua hàng.

    `creator_*` = người lập đơn (`created_by`). `approver_*` = người bấm Duyệt, tra từ
    nhật ký thao tác chứ không có cột riêng — đơn có thể bị hủy duyệt rồi duyệt lại,
    nên lấy dòng GẦN NHẤT.

    Ô "Người nhận" trên mẫu Đơn mua hàng cố ý không có ở đây: hệ thống không có thao tác
    nào ứng với việc nhận hàng tận tay, ô đó để ký tươi lúc giao nhận.
    """
    from app.core.audit import resolve_actor, resolve_signature

    out = {"creator_name": resolve_actor(db, po.created_by),
           "creator_signature": resolve_signature(db, po.created_by),
           "approver_name": "", "approver_signature": ""}
    #  bao-CR-499: cột "Trưởng phòng phê duyệt" giữ người ĐƯỢC CHỌN khi chưa duyệt.
    #  bao-CR-521 (ticket prod #57): đơn CHƯA duyệt thì ô người duyệt trên bản in để TRỐNG HẲN, cả
    #  tên lẫn chữ ký — tên in sẵn đọc ra như đã ký. Duyệt rồi mới in (nhánh dưới).
    from app.core.print_signers import department_head_block, person_block
    stored = person_block(db, int(po.approver_employee_id or 0))
    head = department_head_block(db, int(po.department_id or 0))
    out["dept_head_name"], out["dept_head_signature"] = head["name"], head["signature"]
    if po.status not in _PO_APPROVED_STATUSES:
        return out

    row = service.latest_approved_actor(db, po.id)
    if row and row[0]:
        out["approver_name"] = resolve_actor(db, row[0])
        out["approver_signature"] = resolve_signature(db, row[0])
    if stored["name"]:      # cột thắng nhật ký (bao-CR-490/499)
        out["approver_name"], out["approver_signature"] = stored["name"], stored["signature"]
    return out


def _out_print(db: Session, po: PurchaseOrder) -> dict:
    """Bản in Đơn mua hàng: `_out` + người ký + pháp nhân · NCC · điều khoản · kho nhận."""
    data = _out(db, po)
    data["signers"] = resolve_print_signers(db, po)
    company = service.company_by_id(db, po.company_id) if po.company_id else None
    sup = service.supplier_by_code(db, po.supplier_code)
    data["company"] = {"name": company.name, "address": company.address, "tax_code": company.tax_code,
                       "invoice_email": company.invoice_email} if company else {}
    data["supplier"] = {"name": sup.name, "address": sup.address, "tax_code": sup.tax_code,
                        "payment_terms": sup.payment_terms} if sup else {}
    # bao-CR-321: điều khoản mục 2 + mục 5 của bản in, đã gộp đơn -> NCC -> mặc định ở một chỗ
    data["print_terms"] = service.resolve_print_terms(po, sup)
    # Nơi nhận hàng = kho nhận (lấy kho đầu tiên có trên dòng hàng / lần giao)
    wcode = ""
    for it in data["items"]:
        wcode = it.get("warehouse_code") or next((d.get("warehouse_code") for d in it["deliveries"] if d.get("warehouse_code")), "")
        if wcode:
            break
    wh = service.warehouse_by_code(db, wcode) if wcode else None
    data["warehouse"] = {"code": wh.code, "name": wh.name, "address": wh.address} if wh else {}
    # Map mã kho -> tên kho (cho cột "Tên kho nhập" của Đơn mua hàng)
    codes = {it.get("warehouse_code") for it in data["items"] if it.get("warehouse_code")}
    codes |= {d.get("warehouse_code") for it in data["items"] for d in it["deliveries"] if d.get("warehouse_code")}
    whs = service.warehouses_by_codes(db, list(codes)) if codes else []
    data["wh_names"] = {w.code: w.name for w in whs}
    return data
