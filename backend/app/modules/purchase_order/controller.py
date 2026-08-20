from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import case, func, select, or_
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.ref_filter import apply_ref_filters
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.supplier.model import Supplier
from app.modules.catalog.model import Warehouse
from app.modules.product.model import Product
from app.modules.notification.service import trigger_notification

from . import service
from .model import POItem, PODelivery, PurchaseOrder
from app.modules.payable.model import Payable
from .schema import POCreate, POUpdate, RejectIn, ItemProgressIn, DocumentStatusIn

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_order"])

HEADER = ["id", "code", "misa_code", "pr_code", "survey_code", "company_id", "supplier_code",
          "supplier_name", "department_id", "department", "nspt_id", "nspt", "order_date", "vat_rate", "payment_terms",
          "is_urgent", "status", "document_status", "note", "approve_note"]


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
            "status": d.status, "extra_request": d.extra_request, "progress_note": d.progress_note,
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
            "qty_received": float(it.qty_received or 0), "qty_remaining": float(it.qty_remaining or 0),
            "line_status": it.line_status, "warehouse_code": it.warehouse_code, "note": it.note,
            "progress_status": it.progress_status or "Chưa đặt hàng",
            "pause_reason": it.pause_reason or "", "status_before_pause": it.status_before_pause or "",
            # Giao thiếu: tổng SL đã nhận < SL đặt (dùng cho badge cảnh báo ở FE)
            "is_short_delivery": bool(qty_order > 0 and float(it.qty_received or 0) + 0.001 < qty_order),
            # Tiền theo DÒNG: đặt hàng (SL đặt) · tiền hàng đã nhận (có công nợ) · đã trả · còn lại
            "order_total": round(qty_order * float(it.price or 0) * (1 + float(it.vat or 0) / 100), 2),
            "goods_total": round(sum(x["goods_total"] for x in del_out), 2),
            "paid_total": round(sum(x["paid"] for x in del_out), 2),
            "remaining_total": round(sum(x["remaining"] for x in del_out), 2),
            "deliveries": del_out}


def _out(db: Session, po: PurchaseOrder) -> dict:
    d = {c: getattr(po, c) for c in HEADER}
    d["vat_rate"] = float(po.vat_rate or 0)
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
    # Tổng công nợ CHƯA TRẢ (hàng + vận chuyển) → dùng bật nút Tạo yêu cầu thanh toán
    d["unpaid_total"] = round(sum(float(p.remaining or 0) for p in all_pays), 2)
    return d


def _list_query(request: Request, db: Session, user):
    """Bộ lọc + phạm vi của màn danh sách — dùng chung cho danh sách và xuất Excel (CR-068)."""
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, request, service.FILTERABLE)
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
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    return apply_sort_from_request(q, PurchaseOrder, request)   # sort theo cột; 'amount' tính toán -> bỏ qua


@router.get("")
def list_po(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
            user=Depends(require("purchase_order", "read"))):
    q = _list_query(request, db, user)
    total, items = service.list_po(db, q, pg)
    out = []
    for p in items:
        row = {c: getattr(p, c) for c in HEADER}
        row["created_at"] = p.created_at   # thời điểm tạo (có giờ) — hiển thị giờ VN ở list
        # Tiền hàng ở danh sách = GIÁ TRỊ ĐẶT HÀNG (SL đặt × đơn giá × VAT) — ổn định, không về 0
        # khi dòng chuyển "Đã đặt hàng" mà chưa nhận (it.amount tính theo SL thực nhận).
        row["amount"] = round(sum(
            float(i.qty_order or 0) * float(i.price or 0) * (1 + float(i.vat or 0) / 100)
            for i in service.items_of(db, p.id)), 2)
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
        "line_status": it.line_status, "progress_status": it.progress_status or "Chưa đặt hàng",
    } for po, it in rows]
    return success({"total": total, "items": items})


@router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "read"))):
    scoped = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.get_po(db, pid)))


@router.get("/{pid}/print")
def print_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "print"))):
    po = service.get_po(db, pid)
    data = _out(db, po)
    company = db.get(Company, po.company_id) if po.company_id else None
    sup = db.query(Supplier).filter(Supplier.code == po.supplier_code).first()
    data["company"] = {"name": company.name, "address": company.address, "tax_code": company.tax_code,
                       "invoice_email": company.invoice_email} if company else {}
    data["supplier"] = {"name": sup.name, "address": sup.address, "tax_code": sup.tax_code,
                        "payment_terms": sup.payment_terms} if sup else {}
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


@router.post("")
def create_po(data: POCreate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    return success(_out(db, service.create_po(db, data, user.id)), "Đã tạo đơn mua hàng", 201)


@router.post("/{pid}/copy")
def copy_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.post("/{pid}/clone")
def clone_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS)."""
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.patch("/{pid}")
def update_po(pid: int, data: POUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.update_po(db, pid, data, user.id)), "Đã cập nhật")


@router.patch("/{pid}/document-status")
def set_document_status(pid: int, body: DocumentStatusIn, db: Session = Depends(get_db),
                        user=Depends(require("purchase_order", "write"))):
    """Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành)."""
    po = service.set_document_status(db, pid, body.document_status, user.id)
    return success(_out(db, po), "Đã cập nhật hồ sơ chứng từ")


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    service.delete_po(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_pos(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for pid in id_list:
        try:
            service.delete_po(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa đơn ID {pid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


@router.post("/{pid}/submit")
def submit_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    # CR-073: trước đây gọi thẳng set_status nên gửi duyệt được đơn thiếu NCC, thiếu dòng
    # hàng, hoặc đơn đang ở trạng thái bất kỳ. set_status chỉ GÁN trạng thái, không kiểm gì —
    # chốt phải đặt ở đây (đồng bộ cách làm của submit_pr).
    po = service.get_po(db, pid)
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
    loi_dong = [f"dòng {i} ({it.product_code or 'chưa có mã hàng'}): {', '.join(t)}"
                for i, it in enumerate(items, 1) if (t := service.thieu_truong_dong(it))]
    if loi_dong:
        raise HTTPException(400, "Chưa gửi duyệt được — còn thiếu " + "; ".join(loi_dong) + ".")
    po = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(db=db, event="po_submitted", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         is_urgent=bool(po.is_urgent), link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
               user=Depends(require("purchase_order", "approve"))):
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
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy duyệt")
    po = service.unapprove_po(db, pid, user.id, data.reason.strip())
    return success(_out(db, po), "Đã hủy duyệt — đơn về Nháp")


@router.post("/{pid}/reject")
def reject_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Từ chối = KHÓA đơn (Đã từ chối) — không sửa/gửi lại được, phải Nhân bản thành đơn mới.
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
    _require_awaiting_approval(db, pid, "trả về")
    po = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="po_returned", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã trả đơn về (Bị trả lại)")


@router.post("/{pid}/cancel")
def cancel_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "cancel"))):
    # Hủy phải có lý do
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy đơn")
    # CR-073: đơn đã ở điểm cuối thì không hủy lại được nữa
    if service.get_po(db, pid).status in ("cancelled", "completed"):
        raise HTTPException(400, "Đơn đã Hủy/Hoàn thành — không hủy lại được")
    # Có sản phẩm nào đã Hoàn thành → KHÔNG cho hủy
    if db.query(POItem).filter(POItem.po_id == pid, POItem.progress_status == "Hoàn thành").first():
        raise HTTPException(400, "Đơn có sản phẩm đã Hoàn thành — không thể hủy")
    return success(_out(db, service.set_status(db, pid, "cancelled", user.id, data.reason)), "Đã hủy đơn")


@router.post("/{pid}/complete")
def complete_po(pid: int, db: Session = Depends(get_db),
                user=Depends(require("purchase_order", "write"))):
    # Chỉ cho Hoàn thành ĐƠN khi MỌI dòng đã ở điểm cuối ("Hoàn thành"/"Hủy đơn") —
    # giữ header nhất quán với tiến độ dòng (tránh đơn "Hoàn thành" mà dòng chưa nhập
    # Số HĐ / chưa thanh toán, dẫn tới không tạo được Yêu cầu thanh toán).
    lines = db.query(POItem).filter(POItem.po_id == pid).all()
    pending = [it for it in lines if (it.progress_status or "") not in ("Hoàn thành", "Hủy đơn")]
    if pending:
        names = ", ".join((it.product_name or it.product_code or f"#{it.id}") for it in pending[:5])
        more = f" (+{len(pending) - 5} dòng nữa)" if len(pending) > 5 else ""
        raise HTTPException(
            400,
            f"Còn {len(pending)} dòng chưa Hoàn thành/Hủy: {names}{more}. "
            "Hãy hoàn tất tiến độ từng dòng (nhập Số HĐ → tạo & chi Yêu cầu thanh toán → Hoàn thành dòng) "
            "trước khi hoàn thành đơn.")
    return success(_out(db, service.set_status(db, pid, "completed", user.id)), "Đã hoàn thành đơn")


@router.post("/{pid}/reopen")
def reopen_po(pid: int, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    po = service.reopen_po(db, pid, user.id)
    return success(_out(db, po), "Đã mở lại đơn để xử lý tiếp")


@router.post("/{pid}/items/{item_id}/progress")
def set_item_progress(pid: int, item_id: int, data: ItemProgressIn, db: Session = Depends(get_db),
                      user=Depends(require("purchase_order", "write"))):
    """Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH."""
    return success(_out(db, service.set_item_progress(db, pid, item_id, data.status, data.reason, user.id)),
                   "Đã cập nhật trạng thái dòng")


