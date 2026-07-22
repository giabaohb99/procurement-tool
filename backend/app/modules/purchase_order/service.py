"""Đơn mua hàng: lưu header + dòng hàng + các lần giao; mỗi lần lưu reconcile side-effect
(phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng). Idempotent theo id của dòng giao."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.catalog.model import ItemGroup
from app.modules.goods_receipt import service as gr_service
from app.modules.inventory import service as inv_service
from app.modules.payable import service as pay_service
from app.modules.supplier.model import Supplier

from .model import PODelivery, POItem, PurchaseOrder
from .schema import POCreate, POUpdate


def _pdate(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError:
        return None


def _days(a: str, b: str) -> int:
    """Số ngày = (a − b). a,b là 'YYYY-MM-DD'. Trả 0 nếu thiếu."""
    da, db_ = _pdate(a), _pdate(b)
    return (da - db_).days if da and db_ else 0

FILTERABLE = ["code", "status", "supplier_code", "pr_code", "misa_code", "nspt", "is_urgent", "department", "document_status"]
ENTITY = "purchase_order"


def get_po(db: Session, pid: int) -> PurchaseOrder:
    obj = db.get(PurchaseOrder, pid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy đơn mua hàng")
    return obj


def items_of(db: Session, po_id: int):
    return db.query(POItem).filter(POItem.po_id == po_id).order_by(POItem.id.asc()).all()


def deliveries_of(db: Session, item_id: int):
    return (db.query(PODelivery).filter(PODelivery.po_item_id == item_id)
            .order_by(PODelivery.id.asc()).all())


def list_po(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseOrder.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def _supplier_map(db: Session) -> dict:
    return {s.code: s for s in db.query(Supplier).all()}


def _save_items(db: Session, po: PurchaseOrder, items, user_id: int):
    """Upsert dòng hàng + các lần giao theo id (giữ id ổn định để side-effect idempotent)."""
    if items is None:
        return
    existing_items = {it.id: it for it in items_of(db, po.id)}
    keep_item_ids = set()
    for raw in items:
        delivs = raw.deliveries or []
        data = raw.model_dump(exclude={"deliveries"})
        iid = data.pop("id", None)
        if iid and iid in existing_items:
            it = existing_items[iid]
            # Dòng đã Hoàn thành / Hủy đơn → KHÓA: giữ nguyên, không cho sửa (kể cả lần giao)
            if (it.progress_status or "") in ("Hoàn thành", "Hủy đơn"):
                keep_item_ids.add(it.id)
                continue
            for k, v in data.items():
                setattr(it, k, v)
            it.updated_by = user_id
        else:
            it = POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data)
            db.add(it)
        db.flush()
        keep_item_ids.add(it.id)
        _save_deliveries(db, po, it, delivs, user_id)

    # Xóa dòng hàng (và lần giao + side-effect) không còn trong payload
    for old_id, it in existing_items.items():
        if old_id not in keep_item_ids:
            for d in deliveries_of(db, old_id):
                _cleanup_delivery(db, d.id)
                db.delete(d)
            db.delete(it)
    db.flush()


def _save_deliveries(db: Session, po: PurchaseOrder, item: POItem, delivs, user_id: int):
    existing = {d.id: d for d in deliveries_of(db, item.id)}
    keep = set()
    for raw in delivs:
        data = raw.model_dump()
        did = data.pop("id", None)
        if did and did in existing:
            d = existing[did]
            for k, v in data.items():
                setattr(d, k, v)
            d.updated_by = user_id
        else:
            d = PODelivery(po_id=po.id, po_item_id=item.id, created_by=user_id, updated_by=user_id, **data)
            db.add(d)
        db.flush()
        keep.add(d.id)
    for old_id, d in existing.items():
        if old_id not in keep:
            _cleanup_delivery(db, old_id)
            db.delete(d)
    db.flush()


def _cleanup_delivery(db: Session, delivery_id: int):
    """Gỡ side-effect của 1 lần giao (khi xóa dòng giao)."""
    gr_service.remove_for_delivery(db, delivery_id)
    inv_service.remove_delivery(db, delivery_id)
    pay_service.remove(db, "goods", delivery_id)
    pay_service.remove(db, "shipping", delivery_id)


def recompute_effects(db: Session, po: PurchaseOrder, user_id: int):
    """Tính lại tổng dòng + sinh/cập nhật phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng."""
    suppliers = _supplier_map(db)
    goods_sup = suppliers.get(po.supplier_code)
    goods_days = pay_service.debt_days(po.payment_terms or (goods_sup.payment_terms if goods_sup else ""))

    def _int(x):
        return int("".join(ch for ch in str(x) if ch.isdigit()) or 0)
    _groups = db.query(ItemGroup).all()
    group_std = {g.name: _int(g.std_days) for g in _groups}                       # NCC có sẵn hàng
    group_std_un = {g.name: _int(g.std_days_unavail) or _int(g.std_days) for g in _groups}  # không sẵn

    total_order = total_received = 0.0
    for it in items_of(db, po.id):
        qty_order = float(it.qty_order or 0)
        vat = float(it.vat or 0)

        recv_sum = 0.0
        for d in deliveries_of(db, it.id):
            recv = float(d.received_qty or 0)
            recv_sum += recv
            wh = d.warehouse_code or it.warehouse_code
            if recv > 0:
                # Phiếu nhập kho ngầm + tồn kho
                gr_service.upsert_for_delivery(
                    db, po_id=po.id, po_code=po.code, delivery_id=d.id, company_id=po.company_id,
                    warehouse_code=wh, product_code=it.product_code, product_name=it.product_name,
                    unit=it.unit, qty_received=recv, received_date=d.received_date,
                    qc_result=d.qc_result, user_id=user_id)
                inv_service.apply_delivery(
                    db, delivery_id=d.id, company_id=po.company_id, warehouse_code=wh,
                    product_code=it.product_code, product_name=it.product_name, unit=it.unit,
                    qty=recv, price=float(it.price or 0), user_id=user_id)
                # Công nợ hàng (NCC bán) — số HĐ lấy theo sản phẩm (po_item)
                amt = recv * float(it.price or 0)
                pay_service.upsert(
                    db, source_type="goods", ref_id=d.id, company_id=po.company_id,
                    supplier_code=po.supplier_code, supplier_name=po.supplier_name,
                    po_id=po.id, po_code=po.code, invoice_no=it.invoice_no,
                    incur_date=d.received_date or po.order_date, amount=amt, vat=amt * vat / 100,
                    due_days=goods_days, user_id=user_id)
                # Công nợ vận chuyển (carrier riêng) — chỉ khi có carrier + cước > 0
                ship_amt = float(d.shipping_amount or 0)
                if d.carrier_code and ship_amt > 0:
                    carrier = suppliers.get(d.carrier_code)
                    c_days = pay_service.debt_days(carrier.payment_terms if carrier else "")
                    # Vận chuyển không có hóa đơn riêng → số HĐ tạm = Mã MISA + Mã SP
                    ship_inv = f"{po.misa_code}-{it.product_code}".strip("-")
                    pay_service.upsert(
                        db, source_type="shipping", ref_id=d.id, company_id=po.company_id,
                        supplier_code=d.carrier_code,
                        supplier_name=d.carrier_name or (carrier.name if carrier else ""),
                        po_id=po.id, po_code=po.code, invoice_no=ship_inv,
                        incur_date=d.received_date or po.order_date, amount=ship_amt, vat=0,
                        due_days=c_days, user_id=user_id)
                else:
                    pay_service.remove(db, "shipping", d.id)
            else:
                _cleanup_delivery(db, d.id)

            # Tiến độ giao: số ngày QĐ (theo NCC có sẵn hàng hay không) → ngày QĐ → chênh lệch
            base_std = group_std.get(it.item_group, 0) if it.supplier_ready else group_std_un.get(it.item_group, 0)
            std = base_std or int(d.std_days or 0)   # ưu tiên quy định theo phân loại + có sẵn hàng
            d.std_days = std
            od = _pdate(po.order_date)
            d.regulated_date = (od + timedelta(days=std)).strftime("%Y-%m-%d") if (od and std) else ""
            d.diff_promise = _days(d.promised_date, d.received_date) if (d.promised_date and d.received_date) else 0
            d.diff_regulated = _days(d.regulated_date, d.received_date) if (d.regulated_date and d.received_date) else 0
            d.diff_required = _days(d.regulated_date, it.required_date) if (d.regulated_date and it.required_date) else 0
            ship_q = float(d.ship_qty or 0)
            if recv <= 0:
                d.status = "Chờ giao"
            elif d.qc_result == "Lỗi":
                d.status = "Lỗi"
            elif ship_q > 0 and recv + 0.001 < ship_q:
                d.status = "Giao thiếu"
            else:
                d.status = "Đã nhận"

        it.qty_received = round(recv_sum, 3)
        it.qty_remaining = round(qty_order - recv_sum, 3)
        # Thành tiền đơn hàng = SL THỰC NHẬN × đơn giá × (1+VAT) (đã chốt)
        it.amount = round(recv_sum * float(it.price or 0) * (1 + vat / 100), 2)
        if recv_sum <= 0:
            it.line_status = "Chưa giao"
        elif recv_sum + 0.001 < qty_order:
            it.line_status = "Đang giao"
        else:
            it.line_status = "Đủ"
        total_order += qty_order
        total_received += recv_sum

    # Trạng thái PO theo tiến độ nhận (không hạ cấp khi chưa duyệt)
    if po.status in ("approved", "partial", "received") and total_order > 0:
        if total_received <= 0:
            po.status = "approved"
        elif total_received + 0.001 < total_order:
            po.status = "partial"
        else:
            po.status = "received"
    db.flush()


# Các cột dòng hàng được sao chép khi Nhân bản (KHÔNG copy số đã nhận / lần giao / trạng thái)
_ITEM_COPY_FIELDS = ["product_code", "product_name", "invoice_name", "item_group", "spec",
                     "fg_code", "fg_name", "invoice_no", "supplier_ready", "required_date", "unit",
                     "qty_request", "qty_order", "price", "vat", "warehouse_code", "note"]


def copy_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Nhân bản đơn thành 1 đơn Nháp mới: giữ dòng hàng, bỏ lần giao/số đã nhận, reset mã/MISA/trạng thái."""
    src = get_po(db, pid)
    po = PurchaseOrder(
        code="", misa_code="", pr_code=src.pr_code, survey_code=src.survey_code,
        company_id=src.company_id, supplier_code=src.supplier_code, supplier_name=src.supplier_name,
        department=src.department, nspt=src.nspt, order_date=src.order_date, vat_rate=src.vat_rate,
        payment_terms=src.payment_terms, is_urgent=src.is_urgent, note=src.note,
        status="draft", created_by=user_id, updated_by=user_id,
    )
    db.add(po)
    db.flush()
    po.code = f"PO{po.id:05d}"
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _ITEM_COPY_FIELDS}
        data["amount"] = round((float(data.get("qty_order") or 0)) * (float(data.get("price") or 0)) * (1 + (float(data.get("vat") or 0)) / 100), 2)
        db.add(POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data))
    db.commit()
    db.refresh(po)
    record(db, user_id, ENTITY, po.id, "create", f"Nhân bản từ {src.code}")
    return po


def _default_nspt(db: Session, data: POCreate, user_id: int) -> str:
    """NSPT mặc định khi tạo ĐMH:
    - Tạo TỪ YCMH (pr_code): lấy người phụ trách (assignee) của dòng trong đơn.
    - Không qua YCMH: người tạo đơn.
    """
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    if data.pr_code:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == data.pr_code).first()
        if pr:
            po_codes = {(it.product_code or "").strip() for it in (data.items or []) if (it.product_code or "").strip()}
            rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
            emp_code = ""
            for r in rows:   # ưu tiên dòng khớp sản phẩm trong đơn
                if (r.assignee or "").strip() and (not po_codes or (r.product_code or "").strip() in po_codes):
                    emp_code = r.assignee.strip(); break
            if not emp_code:   # fallback: bất kỳ dòng nào có người phụ trách
                for r in rows:
                    if (r.assignee or "").strip():
                        emp_code = r.assignee.strip(); break
            if emp_code:
                emp = db.query(Employee).filter(Employee.code == emp_code).first()
                if emp:
                    return emp.full_name
    u = db.query(User).filter(User.id == user_id).first()   # người tạo
    if u and u.employee_id:
        emp = db.query(Employee).filter(Employee.id == u.employee_id).first()
        if emp:
            return emp.full_name
    return ""


def create_po(db: Session, data: POCreate, user_id: int) -> PurchaseOrder:
    nspt = (data.nspt or "").strip() or _default_nspt(db, data, user_id)
    po = PurchaseOrder(
        code=data.code or "", misa_code=data.misa_code, pr_code=data.pr_code,
        survey_code=data.survey_code, company_id=data.company_id, supplier_code=data.supplier_code,
        supplier_name=data.supplier_name, department=data.department, nspt=nspt,
        order_date=data.order_date, vat_rate=data.vat_rate, payment_terms=data.payment_terms,
        is_urgent=data.is_urgent, note=data.note, status="draft", created_by=user_id, updated_by=user_id,
    )
    db.add(po)
    db.flush()
    if not po.code:
        po.code = f"PO{po.id:05d}"
    _save_items(db, po, data.items, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    record(db, user_id, ENTITY, po.id, "create")
    return po


def update_po(db: Session, pid: int, data: POUpdate, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status in ("completed", "cancelled"):
        raise HTTPException(400, "Đơn đã hoàn thành/đã hủy — không sửa được. Dùng 'Nhân bản' để tạo đơn mới.")
    old_urgent = bool(po.is_urgent)
    for k, v in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(po, k, v)
    po.updated_by = user_id
    _save_items(db, po, data.items, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    # Cờ Đơn gấp đổi → đồng bộ ngược về YCMH + các ĐMH anh em cùng pr_code (hai chiều)
    if bool(po.is_urgent) != old_urgent and po.pr_code:
        sync_urgent_group(db, po.pr_code, bool(po.is_urgent), exclude_po_id=po.id)
    record(db, user_id, ENTITY, pid, "update")
    try:
        apply_auto_progress(db, po, user_id)   # tự tiến trạng thái dòng + đồng bộ YCMH (chỉ khi có đổi)
    except Exception:
        db.rollback()   # auto-progress không được phép làm hỏng thao tác chính (đã commit)
    # LUÔN đồng bộ lại YCMH sau khi lưu ĐMH — kể cả khi trạng thái dòng KHÔNG đổi nhưng
    # SL đặt/nhận thay đổi (vd sửa SL nhận 1800→1900). apply_auto_progress chỉ sync khi có
    # đổi trạng thái nên nếu thiếu bước này, tiến độ SL bên YCMH sẽ bị cũ.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po


DOCUMENT_STATUSES = ("chưa có chứng từ", "đã có thông tin chứng từ", "đã đủ chứng từ")


def set_document_status(db: Session, pid: int, value: str, user_id: int) -> PurchaseOrder:
    """Task 10b: cập nhật TAY trạng thái hồ sơ chứng từ. Cho phép cả khi đơn đã hoàn thành
    (chứng từ có thể bổ sung sau khi đơn xong)."""
    value = (value or "").strip()
    if value not in DOCUMENT_STATUSES:
        raise HTTPException(400, "Trạng thái hồ sơ chứng từ không hợp lệ")
    po = get_po(db, pid)
    po.document_status = value
    po.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "document_status", value)
    db.refresh(po)
    return po


def delete_po(db: Session, pid: int, user_id: int):
    po = get_po(db, pid)
    from app.modules.attachment.service import delete_attachments_for
    pairs = [("purchase_order", pid)]
    for it in items_of(db, pid):
        for d in deliveries_of(db, it.id):
            pairs.append(("delivery", d.id))
            _cleanup_delivery(db, d.id)
            db.delete(d)
        db.delete(it)
    delete_attachments_for(db, pairs)
    db.delete(po)
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")


def reopen_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Mở lại đơn (từ Hoàn thành) để xử lý tiếp — trả về trạng thái theo TIẾN ĐỘ NHẬN,
    KHÔNG hạ về Nháp (giữ 'đã duyệt' để sửa/nhập Số HĐ + cập nhật tiến độ dòng ngay)."""
    po = get_po(db, pid)
    if po.status != "completed":
        raise HTTPException(400, "Chỉ mở lại đơn đã Hoàn thành.")
    items = items_of(db, pid)
    total_order = sum(float(i.qty_order or 0) for i in items)
    total_recv = sum(float(i.qty_received or 0) for i in items)
    if total_order > 0 and total_recv + 0.001 >= total_order:
        st = "received"
    elif total_recv > 0:
        st = "partial"
    else:
        st = "approved"
    return set_status(db, pid, st, user_id)


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseOrder:
    po = get_po(db, pid)
    po.status = status
    if message:
        po.approve_note = message
    po.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    # Mọi đổi trạng thái ĐƠN đều ảnh hưởng việc đơn có được TÍNH vào YCMH hay không
    # (duyệt → bắt đầu tính; hủy/từ chối → thôi tính) nên luôn đồng bộ lại tiến độ dòng YCMH.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po


# ───────────────────────── Máy trạng thái TIẾN ĐỘ của DÒNG ĐMH (progress_status) ─────────────────────────
# Luồng chính tuần tự; Tạm ngưng/Hủy là ngoại lệ bấm nút, cần lý do.
# Task 8: tách "Chưa gửi ĐMH cho KT" (có số hóa đơn) → "Đã gửi ĐMH cho KT" (có ngày giao chứng từ).
PROGRESS_ORDER = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng",
                  "Chưa gửi ĐMH cho KT", "Đã gửi ĐMH cho KT", "Hoàn thành"]
PROGRESS_EXCEPTIONS = ["Tạm ngưng", "Hủy đơn"]


def is_line_paid(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Điều kiện 'đã thanh toán dòng' = MỌI khoản nợ HÀNG (goods, không tính vận chuyển)
    của các lần giao đã nhận của dòng đều đã trả đủ (còn lại ≈ 0)."""
    from app.modules.payable.model import Payable
    ref_ids = [d.id for d in deliveries_of(db, item.id) if float(d.received_qty or 0) > 0]
    if not ref_ids:
        return False   # chưa nhận hàng thì chưa thể 'đã trả đủ'
    pays = (db.query(Payable)
            .filter(Payable.source_type == "goods", Payable.ref_type == "delivery",
                    Payable.ref_id.in_(ref_ids)).all())
    if not pays:
        return False
    return all(float(p.remaining or 0) <= 0.01 for p in pays)


# Tên trường hiển thị còn thiếu cho từng bước tiến độ (index theo PROGRESS_ORDER)
_STEP_MISSING = {
    1: "Mã đơn MISA (trên phiếu)",
    2: "Có nhận hàng (số lượng nhận > 0)",
    3: "Số hóa đơn",
    4: "Ngày giao chứng từ cho KT",
    5: "Thanh toán cho dòng (NCC sản phẩm)",
}


def _step_ok(db: Session, po: PurchaseOrder, item: POItem, ti: int) -> bool:
    """Điều kiện ĐỦ để dòng đạt bước index ti (dùng chung cho auto-advance + validate_progress)."""
    if ti <= 0:
        return True
    if ti == 1:
        return bool((po.misa_code or "").strip())
    if ti == 2:
        return float(item.qty_received or 0) > 0
    if ti == 3:   # Chưa gửi ĐMH cho KT — đã có số hóa đơn
        return bool((item.invoice_no or "").strip())
    if ti == 4:   # Đã gửi ĐMH cho KT — đã có ngày giao chứng từ
        return bool((item.document_delivery_date or "").strip())
    if ti == 5:   # Hoàn thành — đã thanh toán dòng
        return is_line_paid(db, po, item)
    return False


def validate_progress(db: Session, po: PurchaseOrder, item: POItem, target: str):
    """Trả (ok, missing[]): missing là TÊN TRƯỜNG hiển thị còn thiếu. Điều kiện CỘNG DỒN theo bước."""
    if target not in PROGRESS_ORDER:
        return True, []
    ti = PROGRESS_ORDER.index(target)
    missing = [_STEP_MISSING[s] for s in range(1, ti + 1) if not _step_ok(db, po, item, s)]
    return (len(missing) == 0), missing


def highest_satisfied_step(db: Session, po: PurchaseOrder, item: POItem) -> int:
    """Bước cao nhất LIÊN TỤC thỏa (dừng ở bước hụt đầu tiên — gate cộng dồn)."""
    ti = 0
    for s in range(1, len(PROGRESS_ORDER)):
        if _step_ok(db, po, item, s):
            ti = s
        else:
            break
    return ti


def auto_advance_line(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Chỉ TIẾN (forward-only). Bỏ qua dòng ở điểm cuối/tạm ngưng. Trả True nếu có đổi."""
    if item.progress_status in ("Hoàn thành", "Hủy đơn", "Tạm ngưng"):
        return False
    cur = PROGRESS_ORDER.index(item.progress_status) if item.progress_status in PROGRESS_ORDER else 0
    target = highest_satisfied_step(db, po, item)
    if target > cur:
        item.progress_status = PROGRESS_ORDER[target]
        return True
    return False


def apply_auto_progress(db: Session, po: PurchaseOrder, user_id: int | None = None) -> bool:
    """Duyệt mọi dòng → auto tiến; nếu có đổi thì commit + đồng bộ YCMH. Trả True nếu có đổi."""
    changed = False
    for item in db.query(POItem).filter(POItem.po_id == po.id).all():
        if auto_advance_line(db, po, item):
            changed = True
            record(db, user_id or 0, ENTITY, po.id, "item_progress_auto",
                   f"{item.product_name}: {item.progress_status}")
    if changed:
        db.commit()
        _sync_pr(db, po.pr_code)
    return changed


def set_item_progress(db: Session, pid: int, item_id: int, target: str, reason: str, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status not in ("approved", "partial", "received", "processing", "completed"):
        raise HTTPException(400, "Chỉ cập nhật tiến độ dòng khi đơn đã được duyệt.")
    item = db.query(POItem).filter(POItem.id == item_id, POItem.po_id == pid).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy dòng hàng.")
    if item.progress_status in ("Hủy đơn", "Hoàn thành"):
        done = "hoàn thành" if item.progress_status == "Hoàn thành" else "hủy"
        raise HTTPException(400, f"Dòng đã {done} — không thể đổi trạng thái (điểm cuối).")

    if target == "__resume__":
        # Tiếp tục đơn từ Tạm ngưng → khôi phục trạng thái trước đó
        if item.progress_status != "Tạm ngưng":
            raise HTTPException(400, "Dòng không ở trạng thái Tạm ngưng.")
        item.progress_status = item.status_before_pause or "Chưa đặt hàng"
        item.status_before_pause = ""
    elif target in PROGRESS_EXCEPTIONS:
        if not (reason or "").strip():
            raise HTTPException(400, f"Cần nhập lý do {target.lower()}.")
        if target == "Tạm ngưng":
            item.status_before_pause = item.progress_status
        item.pause_reason = reason.strip()
        item.progress_status = target
    elif target in PROGRESS_ORDER:
        raise HTTPException(400, "Trạng thái tiến độ tự động theo dữ liệu — không đặt tay. Chỉ dùng Tạm ngưng/Hủy đơn/Tiếp tục.")
    else:
        raise HTTPException(400, "Trạng thái không hợp lệ.")

    item.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "item_progress", f"{item.product_name}: {target if target != '__resume__' else 'Tiếp tục'}")
    _sync_pr(db, po.pr_code)   # đồng bộ tiến độ sang YCMH nguồn
    db.refresh(po)
    return po


def sync_urgent_group(db: Session, pr_code: str, is_urgent: bool, *, exclude_po_id: int | None = None) -> None:
    """Đồng bộ cờ Đơn gấp cho cả NHÓM: YCMH + mọi ĐMH cùng pr_code = is_urgent.

    Dùng UPDATE trực tiếp (không đi qua endpoint) nên không gây vòng lặp sync.
    exclude_po_id: bỏ qua chính ĐMH vừa lưu (đã set giá trị rồi)."""
    if not pr_code:
        return
    from app.modules.purchase_request.model import PurchaseRequest
    q = db.query(PurchaseOrder).filter(PurchaseOrder.pr_code == pr_code)
    if exclude_po_id:
        q = q.filter(PurchaseOrder.id != exclude_po_id)
    q.update({PurchaseOrder.is_urgent: is_urgent}, synchronize_session=False)
    db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).update(
        {PurchaseRequest.is_urgent: is_urgent}, synchronize_session=False)
    db.commit()


def _sync_pr(db: Session, pr_code: str) -> None:
    """Đồng bộ tiến độ dòng ĐMH → dòng YCMH nguồn (khớp product_code) + suy lại trạng thái phiếu."""
    if not pr_code:
        return
    try:
        from app.modules.purchase_request import service as pr_service
        pr_service.sync_from_purchase_orders(db, pr_code)
    except Exception:
        pass  # sync không được phép làm hỏng thao tác chính
