from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import case, func, select, or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.ref_filter import apply_ref_filters
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.core.status_codes import (PO_DELIVERY_STATUS, PO_DOCUMENT_STATUS,
                                   PO_ITEM_LINE_STATUS, PO_PROGRESS_STATUS)
from app.modules.company.model import Company
from app.modules.supplier.model import Supplier
from app.modules.catalog.model import Warehouse
from app.modules.product.model import Product
from app.modules.notification.service import trigger_notification

from . import service
from .model import (ALLOCATION_METHOD_LABELS, AllocationMethod, DEFAULT_CURRENCY,
                    IMPORT_COST_STATUS_LABELS, IMPORT_COST_TYPE_LABELS, ImportCostStatus,
                    ImportCostType, ORDER_TYPE_LABELS, OrderType,
                    POItem, PODelivery, PurchaseOrder)
from app.modules.payable.model import Payable
from .schema import POCreate, POUpdate, RejectIn, ItemProgressIn, DocumentStatusIn

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_order"])

HEADER = ["id", "code", "misa_code", "pr_code", "survey_code", "company_id", "supplier_code",
          "supplier_name", "department_id", "department", "nspt_id", "nspt", "order_date", "vat_rate", "payment_terms",
          "is_urgent", "status", "document_status", "note", "approve_note",
          "order_type", "currency", "customs_decl_no", "customs_decl_date", "etd_date",
          "inspection_days", "return_days", "invoice_deadline"]


def _in_scope(db: Session, pid: int, user, action: str) -> PurchaseOrder:
    """Nạp ĐMH theo id NHƯNG chỉ khi nó nằm trong phạm vi `action` của người gọi.

    `require(entity, action)` chỉ trả lời "vai trò này được làm hành động đó không"; nó
    KHÔNG biết đơn thuộc pháp nhân nào. Trước bản vá này mọi nhánh GHI/IN dừng ở
    `service.get_po` = `db.get` trần, nên đổi đuôi URL sang `/print` là vòng qua được đúng
    bộ lọc mà `GET /{pid}` ngay bên trên đã đặt.

    `action` PHẢI khớp `require(...)` của route gọi (in → `print`, duyệt → `approve`, …);
    lấy `read` cho tất cả là mượn phạm vi rộng hơn phạm vi thật của hành động.

    404 cho cả "không có" lẫn "ngoài phạm vi" — cùng mã lỗi `service.get_po` vẫn trả, nên
    người ngoài phạm vi không suy ra được đơn có thật hay không.
    """
    po = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                     PurchaseOrder, "purchase_order", user,
                     get_perm_profile(db, user), action).first()
    if not po:
        raise HTTPException(404, "Không tìm thấy đơn mua hàng")
    return po


def _require_awaiting_approval(db: Session, pid: int, action_label: str) -> None:
    """CR-073: duyệt / từ chối / trả về chỉ hợp lệ khi đơn đang CHỜ DUYỆT.

    Trước đây các endpoint này gọi thẳng `service.set_status`, mà hàm đó chỉ GÁN trạng thái
    chứ không kiểm gì — nên gọi API trực tiếp là chuyển đơn sang trạng thái bất kỳ, kể cả
    ngược chiều (đơn đã Hoàn thành vẫn "duyệt" lại được). Giao diện có ẩn nút, nhưng ẩn nút
    không phải là chốt chặn.
    """
    if service.get_po(db, pid).status != "submitted":
        raise HTTPException(400, f"Chỉ {action_label} được đơn đang ở trạng thái Chờ duyệt")


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


def _import_cost(c, pay: Payable | None = None) -> dict:
    """Một dòng chi phí nhập khẩu — trả cả SỐ lẫn NHÃN (R2/QĐ-11).

    `pay` là khoản nợ của dòng (bao-CR-319 P5), None khi đơn chưa duyệt / dòng chưa thành nợ:
    khi đó `payable_id = 0`, đã chi 0 và còn lại = tổng dòng để giao diện vẫn cộng được.
    """
    try:
        cost_type = ImportCostType(int(c.cost_type or 0))
    except ValueError:
        cost_type = ImportCostType.OTHER
    try:
        alloc = AllocationMethod(int(c.allocation_method or 0))
    except ValueError:
        alloc = AllocationMethod.BY_VALUE
    # bao-CR-347 — dòng cũ chưa có cột này đọc thành Thực tế, cùng chiều với `is_actual_cost`.
    cost_status = (ImportCostStatus.ESTIMATED if not service.is_actual_cost(c)
                   else ImportCostStatus.ACTUAL)
    base_amount = float(c.base_amount or 0) or service.import_cost_base(c)
    paid = float(pay.paid_amount or 0) if pay else 0.0
    return {"id": c.id, "cost_type": int(cost_type), "cost_type_label": IMPORT_COST_TYPE_LABELS.get(cost_type, ""),
            "cost_status": int(cost_status),
            "cost_status_label": IMPORT_COST_STATUS_LABELS.get(cost_status, ""),
            "payable_id": pay.id if pay else 0,
            "paid_amount": round(paid, 2),
            "remaining": round(float(pay.remaining or 0), 2) if pay else round(base_amount, 2),
            "payable_status": (pay.status or "") if pay else "",
            "description": c.description or "",
            "supplier_code": c.supplier_code or "", "supplier_name": c.supplier_name or "",
            # `amount` NGUYÊN TỆ và chưa gồm VAT; `base_amount` đã gồm VAT và đã quy đổi.
            "currency": c.currency or DEFAULT_CURRENCY, "exchange_rate": service.rate_of(c),
            "amount": float(c.amount or 0), "vat": float(c.vat or 0),
            "base_amount": base_amount,
            "allocation_method": int(alloc),
            "allocation_method_label": ALLOCATION_METHOD_LABELS.get(alloc, ""),
            "allocation_target": c.allocation_target or "",
            "manual_allocation": service.parse_manual_allocation(getattr(c, "manual_allocation", "")),
            "invoice_no": c.invoice_no or "", "invoice_date": c.invoice_date or "",
            "payment_due_date": c.payment_due_date or "", "note": c.note or ""}


def _import_cost_summary(rows: list[dict], goods_base: float) -> dict:
    """Cụm tổng chi phí của lô hàng — gom theo LOẠI và theo NHÀ CUNG CẤP.

    Gom sẵn ở backend vì P5 sẽ tạo Yêu cầu thanh toán gom theo NCC từ đúng con số này;
    để giao diện tự cộng thì hai nơi dễ lệch nhau. Mọi số ở đây đã quy đổi về VNĐ.

    bao-CR-347: mọi con số TỔNG ở đây chỉ đếm dòng THỰC TẾ. Giao diện KHÔNG còn chỗ đặt một
    khoản thành Dự kiến (đại ca chốt 10/09/2026 bỏ hẳn khái niệm đó khỏi màn hình), nên trên
    thực tế phép lọc này không loại dòng nào — giữ lại để dữ liệu lỡ có dòng dự kiến từ đợt
    thử nghiệm cũng không lọt vào công nợ.
    """
    actual = [r for r in rows if int(r.get("cost_status") or 0) != int(ImportCostStatus.ESTIMATED)]
    cost_total = round(sum(r["base_amount"] for r in actual), 2)
    paid_total = round(sum(r["paid_amount"] for r in actual), 2)
    by_type: dict[int, dict] = {}
    by_supplier: dict[str, dict] = {}
    for r in actual:
        g = by_type.setdefault(r["cost_type"], {"cost_type": r["cost_type"],
                                                "cost_type_label": r["cost_type_label"],
                                                "base_amount": 0.0, "count": 0})
        g["base_amount"] = round(g["base_amount"] + r["base_amount"], 2)
        g["count"] += 1
        code = r["supplier_code"] or ""
        # P5: mỗi NCC một dòng tổng · đã chi · còn lại + danh sách id khoản nợ CÒN NỢ để nút
        # "Tạo yêu cầu thanh toán" của NCC đó đưa thẳng sang màn lập phiếu (mỗi phiếu một NCC).
        n = by_supplier.setdefault(code, {"supplier_code": code, "supplier_name": r["supplier_name"],
                                          "base_amount": 0.0, "paid_amount": 0.0, "remaining": 0.0,
                                          "count": 0, "unpaid_payable_ids": []})
        n["base_amount"] = round(n["base_amount"] + r["base_amount"], 2)
        n["paid_amount"] = round(n["paid_amount"] + r["paid_amount"], 2)
        n["remaining"] = round(n["remaining"] + r["remaining"], 2)
        n["count"] += 1
        if r["payable_id"] and r["remaining"] > 0.01:
            n["unpaid_payable_ids"].append(r["payable_id"])
        if not n["supplier_name"]:
            n["supplier_name"] = r["supplier_name"]
    return {
        "goods_base_total": round(goods_base, 2),          # tiền HÀNG đã quy đổi (theo SL đặt)
        "cost_total": cost_total,                          # tổng chi phí THỰC TẾ đã quy đổi
        "paid_total": paid_total,                          # đã chi cho chi phí (P5)
        "remaining_total": round(cost_total - paid_total, 2),  # còn phải chi (P5)
        "landed_total": round(goods_base + cost_total, 2),  # tổng giá vốn lô hàng về tới kho
        "by_type": sorted(by_type.values(), key=lambda x: -x["base_amount"]),
        "by_supplier": sorted(by_supplier.values(), key=lambda x: -x["base_amount"]),
    }


def _out(db: Session, po: PurchaseOrder) -> dict:
    d = {c: getattr(po, c) for c in HEADER}
    d["vat_rate"] = float(po.vat_rate or 0)
    # `document_status` là MÃ (B-06) — trước đây nó là chữ tiếng Việt VIẾT THƯỜNG nên mỗi màn
    # lại tự viết hoa một kiểu ("Đã có chứng từ" ở ô lọc, "đã có thông tin chứng từ" ở bảng).
    d["document_status_label"] = PO_DOCUMENT_STATUS.label_of(po.document_status)
    # bao-CR-319 — loại đơn: trả cả SỐ lẫn NHÃN, tiếng Việt chỉ nằm ở tầng hiển thị (R2/QĐ-11)
    d["order_type"] = int(po.order_type or OrderType.DOMESTIC)
    d["order_type_label"] = ORDER_TYPE_LABELS.get(OrderType(d["order_type"]), "")
    d["currency"] = po.currency or DEFAULT_CURRENCY
    d["exchange_rate"] = service.rate_of(po)
    # Công nợ theo lần giao: HÀNG (goods) hiện đã trả/còn lại trên dòng; gom cả VẬN CHUYỂN cho tổng chưa trả
    all_pays = db.query(Payable).filter(Payable.po_id == po.id, Payable.ref_type == "delivery").all()
    pay_by_del = {p.ref_id: p for p in all_pays if p.source_type == "goods"}
    it_list = service.items_of(db, po.id)
    # Nạp sẵn "tên trên hóa đơn" từ sản phẩm master cho các dòng đang trống (tránh N+1)
    need_codes = {(it.product_code or "").strip() for it in it_list
                  if not (it.invoice_name or "").strip() and (it.product_code or "").strip()}
    inv_by_code = {p.code: (p.invoice_name or "")
                   for p in db.query(Product).filter(Product.code.in_(need_codes)).all()} if need_codes else {}
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
    # bao-CR-319 P3 — chi phí lô hàng nhập khẩu. Trả cho MỌI đơn (đơn trong nước ra mảng
    # rỗng) để giao diện không phải rẽ nhánh đọc dữ liệu; việc ẩn/hiện là chuyện hiển thị.
    cost_pays = service.import_cost_payables_of(db, po.id)
    costs = [_import_cost(c, cost_pays.get(c.id)) for c in service.import_costs_of(db, po.id)]
    # Tổng công nợ CHƯA TRẢ (hàng + vận chuyển + chi phí lô hàng) → dùng bật nút Tạo yêu cầu thanh toán
    d["unpaid_total"] = round(sum(float(p.remaining or 0) for p in all_pays)
                              + sum(float(p.remaining or 0) for p in cost_pays.values()), 2)
    d["import_costs"] = costs
    goods_base = round(sum(i["order_total"] * i["exchange_rate"] for i in items), 2)
    d["import_cost_summary"] = _import_cost_summary(costs, goods_base)
    # bao-CR-319 P4 — chi phí chia về từng dòng hàng, CHỈ ĐỂ XEM (không lưu, không vào kho).
    # Tính ở đây để màn hình, bản in và Yêu cầu thanh toán (P5) đọc cùng một con số.
    # bao-CR-347: chỉ chia dòng THỰC TẾ — giá vốn dòng hàng phải là số thật, số dự toán có
    # đường riêng ở báo cáo giá vốn.
    d["import_cost_allocation"] = service.allocate_import_costs(items, service.actual_costs(costs))
    return d


def _list_query(request: Request, db: Session, user):
    """Bộ lọc + phạm vi của màn danh sách — dùng chung cho danh sách và xuất Excel (CR-068)."""
    # `code` chỉ bị loại khỏi lọc TRẦN (nhường cho ô tìm kiếm đa trường), bộ lọc điều kiện
    # `code__contains=...` vẫn phải chạy -> truyền FILTERABLE đầy đủ cho vế operator.
    filterable = [f for f in service.FILTERABLE if f != "code"]
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, request, filterable,
                      operator_filterable=service.FILTERABLE)
    q = apply_ref_filters(q, PurchaseOrder, request, db)      # CR-088: `nspt_id` / `department_id`
    q = apply_range_filters(q, PurchaseOrder, request, ["order_date"])
    q = apply_equals(q, PurchaseOrder, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(POItem.po_id).where(POItem.item_group.like(f"%{item_group}%"))
        q = q.filter(PurchaseOrder.id.in_(sub))
    invoice_no = (request.query_params.get("invoice_no") or "").strip()
    if invoice_no:
        sub2_item = select(POItem.po_id).where(POItem.invoice_no.like(f"%{invoice_no}%"))
        sub2_deliv = select(PODelivery.po_id).where(PODelivery.invoice_no.like(f"%{invoice_no}%"))
        q = q.filter(or_(PurchaseOrder.id.in_(sub2_item), PurchaseOrder.id.in_(sub2_deliv)))
    # Ô tìm kiếm nhanh: Tìm theo Mã ĐMH, Mã MISA, Mã PYC, Nhà cung cấp, Mã SP hoặc Tên SP ở dòng hàng
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product") or "").strip()
    if search:
        like = f"%{search}%"
        matching_ids = [
            r[0] for r in db.query(POItem.po_id)
            .filter(or_(POItem.product_code.like(like), POItem.product_name.like(like))).all()
            if r[0]
        ]
        conds = [
            PurchaseOrder.code.like(like),
            PurchaseOrder.pr_code.like(like),
            PurchaseOrder.misa_code.like(like),
            PurchaseOrder.supplier_name.like(like),
            PurchaseOrder.supplier_code.like(like),
        ]
        if matching_ids:
            conds.append(PurchaseOrder.id.in_(matching_ids))
        q = q.filter(or_(*conds))
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    return apply_sort_from_request(q, PurchaseOrder, request)


@router.get("")
def list_po(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
            user=Depends(require("purchase_order", "read"))):
    q = _list_query(request, db, user)
    total, items = service.list_po(db, q, pg)
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
        row["amount"] = round(sum(
            float(i.qty_order or 0) * float(i.price or 0) * (1 + float(i.vat or 0) / 100)
            * service.rate_of(i) for i in service.items_of(db, p.id)), 2)
        row["order_type"] = int(p.order_type or OrderType.DOMESTIC)
        row["order_type_label"] = ORDER_TYPE_LABELS.get(OrderType(row["order_type"]), "")
        out.append(row)
    # Gắn pr_id (id phiếu YCMH theo mã PYC) để FE điều hướng sang chi tiết PYC khi click Mã PYC
    codes = {r["pr_code"] for r in out if r.get("pr_code")}
    if codes:
        from app.modules.purchase_request.model import PurchaseRequest
        id_by_code = {c: i for i, c in db.query(PurchaseRequest.id, PurchaseRequest.code)
                      .filter(PurchaseRequest.code.in_(codes)).all()}
        for r in out:
            r["pr_id"] = id_by_code.get(r.get("pr_code"))
    return success({"total": total, "items": out})


@router.get("/export/xlsx")
def export_xlsx(request: Request, ids: str = "", cols: str = "",
                db: Session = Depends(get_db), user=Depends(require("purchase_order", "export"))):
    """CR-068 — xuất Excel danh sách ĐMH, cột dòng hàng lấy đúng bộ cột màn Tiến độ mua hàng
    (một hàng = một lần giao).

    `ids` = đơn người dùng tick chọn; rỗng thì theo bộ lọc đang đặt. `cols` = cột đang hiện.
    Cũng như `/lines`, phải khai báo TRƯỚC `/{pid}`.
    """
    from app.core.auth import user_has_permission
    from app.core.export_xlsx import check_row_limit, parse_ids, pick_columns, xlsx_response
    from . import export as ex

    q = _list_query(request, db, user)
    id_list = parse_ids(ids)
    if id_list:
        q = q.filter(PurchaseOrder.id.in_(id_list))
    pos = q.order_by(PurchaseOrder.id.desc()).all()
    check_row_limit(len(pos))
    show_supplier = user_has_permission(db, user, "supplier", "read")
    rows = ex.build_rows(db, pos, show_supplier)
    check_row_limit(len(rows))
    columns = pick_columns(ex.HEADER_COLS, cols) + ex.line_columns(show_supplier)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


# PHẢI khai báo TRƯỚC `/{pid}`, nếu không "lines" sẽ rơi vào route đó và lỗi ép kiểu int.
@router.get("/lines")
def list_po_lines(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("purchase_order", "read"))):
    """Danh sách DÒNG HÀNG của các đơn mua hàng — dùng cho trang chi tiết Kho.

    `warehouse_code`: lấy dòng có "Kho nhận mặc định" là kho này, HOẶC có lần giao về kho này
    (lần giao đổi kho so với mặc định vẫn là hàng thực về kho → không được bỏ sót).
    `qty_received_here` = SL đã nhận riêng ở kho đang xem (khác qty_received là tổng mọi kho):
    tổng SL nhận của các lần giao ghi rõ kho này, cộng phần đã nhận CHƯA gắn kho nào —
    phần đó quy về kho mặc định của dòng (dữ liệu nhập lịch sử chỉ có SL nhận trên dòng,
    không tách lần giao, nếu bỏ qua thì kho nào cũng hiện 0).
    """
    wh = (request.query_params.get("warehouse_code") or "").strip()
    q = db.query(PurchaseOrder, POItem).join(POItem, POItem.po_id == PurchaseOrder.id)
    if wh:
        by_delivery = select(PODelivery.po_item_id).where(PODelivery.warehouse_code == wh)
        q = q.filter(or_(POItem.warehouse_code == wh, POItem.id.in_(by_delivery)))
    kw = (request.query_params.get("q") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter(or_(PurchaseOrder.code.like(like), POItem.product_code.like(like),
                         POItem.product_name.like(like)))
    progress = (request.query_params.get("progress_status") or "").strip()
    if progress:
        q = q.filter(POItem.progress_status == progress)
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))

    total = q.count()
    rows = (q.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.id.desc(), POItem.id.asc())
            .offset(pg["offset"]).limit(pg["limit"]).all())

    # SL nhận theo lần giao, gom theo dòng: (nhận tại kho đang xem, nhận đã gắn kho bất kỳ)
    recv: dict[int, tuple[float, float]] = {}
    if wh and rows:
        item_ids = [it.id for _, it in rows]
        recv = {
            iid: (float(here or 0), float(assigned or 0)) for iid, here, assigned in
            db.query(
                PODelivery.po_item_id,
                func.sum(case((PODelivery.warehouse_code == wh, PODelivery.received_qty), else_=0)),
                func.sum(case((PODelivery.warehouse_code != "", PODelivery.received_qty), else_=0)),
            ).filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all()
        }

    def _recv_here(it: POItem) -> float:
        here, assigned = recv.get(it.id, (0.0, 0.0))
        if it.warehouse_code == wh:   # phần đã nhận chưa gắn lần giao/kho nào → về kho mặc định
            here += max(0.0, float(it.qty_received or 0) - assigned)
        return round(here, 3)

    items = [{
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
    return success({"total": total, "items": items})


@router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "read"))):
    scoped = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.get_po(db, pid)))


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
    from app.modules.audit.model import AuditLog

    out = {"creator_name": resolve_actor(db, po.created_by),
           "creator_signature": resolve_signature(db, po.created_by),
           "approver_name": "", "approver_signature": ""}
    if po.status not in _PO_APPROVED_STATUSES:
        return out

    row = (db.query(AuditLog.created_by)
           .filter(AuditLog.entity == service.ENTITY, AuditLog.entity_id == po.id,
                   AuditLog.action == "approved")
           .order_by(AuditLog.id.desc()).first())
    if row and row[0]:
        out["approver_name"] = resolve_actor(db, row[0])
        out["approver_signature"] = resolve_signature(db, row[0])
    return out


@router.get("/{pid}/print")
def print_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "print"))):
    po = _in_scope(db, pid, user, "print")
    data = _out(db, po)
    data["signers"] = resolve_print_signers(db, po)
    company = db.get(Company, po.company_id) if po.company_id else None
    sup = db.query(Supplier).filter(Supplier.code == po.supplier_code).first()
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
    wh = db.query(Warehouse).filter(Warehouse.code == wcode).first() if wcode else None
    data["warehouse"] = {"code": wh.code, "name": wh.name, "address": wh.address} if wh else {}
    # Map mã kho -> tên kho (cho cột "Tên kho nhập" của Đơn mua hàng)
    codes = {it.get("warehouse_code") for it in data["items"] if it.get("warehouse_code")}
    codes |= {d.get("warehouse_code") for it in data["items"] for d in it["deliveries"] if d.get("warehouse_code")}
    whs = db.query(Warehouse).filter(Warehouse.code.in_(list(codes))).all() if codes else []
    data["wh_names"] = {w.code: w.name for w in whs}
    return success(data)


@router.get("/{pid}/purchase-request")
def get_po_purchase_request(pid: int, db: Session = Depends(get_db),
                            user=Depends(require("purchase_order", "print"))):
    """Phiếu YCMH nguồn của đơn, đã cắt còn đúng các dòng hàng có trên đơn — bao-CR-314.

    Cổng đặt ở ĐƠN MUA HÀNG chứ không ở phiếu yêu cầu, cố ý: một phiếu YCMH chia cho nhiều
    NSTM phụ trách (`tab_purchase_request_item.assignee`) nên phạm vi dữ liệu của người cầm
    đơn thường KHÔNG với tới cả phiếu — gọi thẳng `/api/purchase-requests/{id}` là 403 đúng
    những người cần in. Ai mở được đơn (quyền `print` + đơn nằm trong phạm vi) thì in được
    phần phiếu tương ứng, và không thấy hàng của người khác vì danh sách đã cắt theo mã hàng
    trên đơn. Luật che NCC cụm `pur` (Task 4) giữ nguyên vì vẫn đi qua `_out` của YCMH.
    """
    scoped = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    po = service.get_po(db, pid)
    pr_code = (po.pr_code or "").strip()
    if not pr_code:
        raise HTTPException(404, "Đơn mua hàng này không gắn phiếu yêu cầu mua hàng")
    #  Nhập trong hàm: `purchase_request.controller` nạp cả cụm model/serializer của YCMH,
    #  kéo lên đầu tệp là buộc hai controller phụ thuộc vòng nhau lúc `app.main` dựng router.
    from app.modules.purchase_request.controller import _out as pr_out
    from app.modules.purchase_request.model import PurchaseRequest
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code,
                                          PurchaseRequest.is_deleted == False).first()  # noqa: E712
    if not pr:
        raise HTTPException(404, f"Không tìm thấy phiếu yêu cầu mua hàng {pr_code}")
    data = service.pr_items_for_po(pr_out(db, pr, user), service.items_of(db, po.id))
    data["po_code"] = po.code
    return success(data)


@router.post("")
def create_po(data: POCreate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    return success(_out(db, service.create_po(db, data, user.id)), "Đã tạo đơn mua hàng", 201)


@router.post("/{pid}/copy")
def copy_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.post("/{pid}/clone")
def clone_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS)."""
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.patch("/{pid}")
def update_po(pid: int, data: POUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "write"))):
    _in_scope(db, pid, user, "write")
    return success(_out(db, service.update_po(db, pid, data, user.id)), "Đã cập nhật")


@router.patch("/{pid}/document-status")
def set_document_status(pid: int, body: DocumentStatusIn, db: Session = Depends(get_db),
                        user=Depends(require("purchase_order", "write"))):
    """Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành)."""
    _in_scope(db, pid, user, "write")
    po = service.set_document_status(db, pid, body.document_status, user.id)
    return success(_out(db, po), "Đã cập nhật hồ sơ chứng từ")


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    _in_scope(db, pid, user, "delete")
    service.delete_po(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_pos(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn của `contract/controller.py`) — lặp theo id trần
    # thì gửi đại một dãy số là xóa được đơn Nháp của pháp nhân khác.
    rows = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(id_list)),
                       PurchaseOrder, "purchase_order", user,
                       get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    for pid in [r.id for r in rows]:
        try:
            service.delete_po(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa đơn ID {pid}: {str(e)}")
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên.
    return success(None, f"Đã xóa {len(rows)} bản ghi")


@router.post("/{pid}/submit")
def submit_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    # CR-073: trước đây gọi thẳng set_status nên gửi duyệt được đơn thiếu NCC, thiếu dòng
    # hàng, hoặc đơn đang ở trạng thái bất kỳ. set_status chỉ GÁN trạng thái, không kiểm gì —
    # chốt phải đặt ở đây (đồng bộ cách làm của submit_pr).
    po = _in_scope(db, pid, user, "write")
    if po.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt được đơn ở trạng thái Nháp hoặc Bị trả lại")
    missing = []
    if not (po.supplier_code or "").strip():
        missing.append("nhà cung cấp")
    items = db.query(POItem).filter(POItem.po_id == pid).order_by(POItem.id).all()
    if not items:
        missing.append("ít nhất một dòng hàng")
    if missing:
        raise HTTPException(400, f"Chưa gửi duyệt được — đơn còn thiếu {' và '.join(missing)}.")
    # CR-095: từng dòng hàng phải điền đủ bộ trường bắt buộc. Nêu ĐÍCH DANH dòng nào
    # thiếu ô nào — báo chung chung thì người lập phải mở lần lượt từng dòng để dò.
    line_errors = [f"dòng {i} ({it.product_code or 'chưa có mã hàng'}): {', '.join(t)}"
                for i, it in enumerate(items, 1) if (t := service.missing_line_fields(it))]
    if line_errors:
        raise HTTPException(400, "Chưa gửi duyệt được — còn thiếu " + "; ".join(line_errors) + ".")
    po = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(db=db, event="po_submitted", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         is_urgent=bool(po.is_urgent), link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
               user=Depends(require("purchase_order", "approve"))):
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "duyệt")
    po = service.set_status(db, pid, "approved", user.id)
    trigger_notification(db=db, event="po_approved", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã duyệt")


@router.post("/{pid}/unapprove")
def unapprove_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
                 user=Depends(require("purchase_order", "approve"))):
    """Hủy duyệt — đơn về Nháp để sửa rồi gửi duyệt lại (CR-108, phiếu hỗ trợ TK19082604).

    Chỉ người có quyền DUYỆT được bấm: sau khi duyệt, đơn là cam kết đã ký với NCC, mở
    lại để sửa là quyết định của trưởng phòng chứ không phải của người lập đơn.
    """
    _in_scope(db, pid, user, "approve")
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy duyệt")
    po = service.unapprove_po(db, pid, user.id, data.reason.strip())
    return success(_out(db, po), "Đã hủy duyệt — đơn về Nháp")


@router.post("/{pid}/reject")
def reject_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Từ chối = KHÓA đơn (Đã từ chối) — không sửa/gửi lại được, phải Nhân bản thành đơn mới.
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "từ chối")
    po = service.set_status(db, pid, "cancelled", user.id, data.reason)
    trigger_notification(db=db, event="po_rejected", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã từ chối")


@router.post("/{pid}/return")
def return_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Trả về = Bị trả lại — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCMH).
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "trả về")
    po = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="po_returned", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã trả đơn về (Bị trả lại)")


@router.post("/{pid}/cancel")
def cancel_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "cancel"))):
    _in_scope(db, pid, user, "cancel")
    # Hủy phải có lý do
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy đơn")
    # CR-073: đơn đã ở điểm cuối thì không hủy lại được nữa
    if service.get_po(db, pid).status in ("cancelled", "completed"):
        raise HTTPException(400, "Đơn đã Hủy/Hoàn thành — không hủy lại được")
    # Có sản phẩm nào đã Hoàn thành → KHÔNG cho hủy
    if db.query(POItem).filter(POItem.po_id == pid,
                               POItem.progress_status == service.PROG_COMPLETED).first():
        raise HTTPException(400, "Đơn có sản phẩm đã Hoàn thành — không thể hủy")
    return success(_out(db, service.set_status(db, pid, "cancelled", user.id, data.reason)), "Đã hủy đơn")


@router.post("/{pid}/complete")
def complete_po(pid: int, db: Session = Depends(get_db),
                user=Depends(require("purchase_order", "write"))):
    # Chỉ cho Hoàn thành ĐƠN khi MỌI dòng đã ở điểm cuối (`completed`/`cancelled`) —
    # giữ header nhất quán với tiến độ dòng (tránh đơn đã hoàn thành mà dòng chưa nhập
    # Số HĐ / chưa thanh toán, dẫn tới không tạo được Yêu cầu thanh toán).
    _in_scope(db, pid, user, "write")
    lines = db.query(POItem).filter(POItem.po_id == pid).all()
    pending = [it for it in lines
               if (it.progress_status or "") not in (service.PROG_COMPLETED, service.PROG_CANCELLED)]
    if pending:
        names = ", ".join((it.product_name or it.product_code or f"#{it.id}") for it in pending[:5])
        more = f" (+{len(pending) - 5} dòng nữa)" if len(pending) > 5 else ""
        raise HTTPException(
            400,
            f"Còn {len(pending)} dòng chưa Hoàn thành/Hủy: {names}{more}. "
            "Hãy hoàn tất tiến độ từng dòng (nhập Số HĐ → tạo & chi Yêu cầu thanh toán → Hoàn thành dòng) "
            "trước khi hoàn thành đơn.")
    # bao-CR-319: đơn nhập khẩu còn phải trả đủ chi phí lô hàng (cước, thuế, phí) mới được đóng.
    service.block_complete_unpaid_import_costs(db, service.get_po(db, pid))
    return success(_out(db, service.set_status(db, pid, "completed", user.id)), "Đã hoàn thành đơn")


@router.post("/{pid}/reopen")
def reopen_po(pid: int, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    _in_scope(db, pid, user, "write")
    po = service.reopen_po(db, pid, user.id)
    return success(_out(db, po), "Đã mở lại đơn để xử lý tiếp")


@router.post("/{pid}/items/{item_id}/progress")
def set_item_progress(pid: int, item_id: int, data: ItemProgressIn, db: Session = Depends(get_db),
                      user=Depends(require("purchase_order", "write"))):
    """Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH."""
    _in_scope(db, pid, user, "write")
    return success(_out(db, service.set_item_progress(db, pid, item_id, data.status, data.reason, user.id)),
                   "Đã cập nhật trạng thái dòng")


