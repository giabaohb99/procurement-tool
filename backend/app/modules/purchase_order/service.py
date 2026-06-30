"""Đơn mua hàng: lưu header + dòng hàng + các lần giao; mỗi lần lưu reconcile side-effect
(phiếu nhập kho ngầm, tồn kho, công nợ 2 luồng). Idempotent theo id của dòng giao."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.goods_receipt import service as gr_service
from app.modules.inventory import service as inv_service
from app.modules.payable import service as pay_service
from app.modules.supplier.model import Supplier

from .model import PODelivery, POItem, PurchaseOrder
from .schema import POCreate, POUpdate

FILTERABLE = ["code", "status", "supplier_code", "pr_code"]
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
    goods_days = pay_service.debt_days(goods_sup.payment_terms if goods_sup else "")

    total_order = total_received = 0.0
    for it in items_of(db, po.id):
        qty_order = float(it.qty_order or 0)
        vat = float(it.vat or 0)
        it.amount = round(qty_order * float(it.price or 0) * (1 + vat / 100), 2)

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
                    qty=recv, user_id=user_id)
                # Công nợ hàng (NCC bán)
                amt = recv * float(it.price or 0)
                pay_service.upsert(
                    db, source_type="goods", ref_id=d.id, company_id=po.company_id,
                    supplier_code=po.supplier_code, supplier_name=po.supplier_name,
                    po_id=po.id, po_code=po.code, invoice_no=d.invoice_no,
                    incur_date=d.received_date, amount=amt, vat=amt * vat / 100,
                    due_days=goods_days, user_id=user_id)
                # Công nợ vận chuyển (carrier riêng) — chỉ khi có carrier + cước > 0
                ship_amt = float(d.shipping_amount or 0)
                if d.carrier_code and ship_amt > 0:
                    carrier = suppliers.get(d.carrier_code)
                    c_days = pay_service.debt_days(carrier.payment_terms if carrier else "")
                    pay_service.upsert(
                        db, source_type="shipping", ref_id=d.id, company_id=po.company_id,
                        supplier_code=d.carrier_code,
                        supplier_name=d.carrier_name or (carrier.name if carrier else ""),
                        po_id=po.id, po_code=po.code, invoice_no=d.invoice_no,
                        incur_date=d.received_date, amount=ship_amt, vat=0,
                        due_days=c_days, user_id=user_id)
                else:
                    pay_service.remove(db, "shipping", d.id)
            else:
                _cleanup_delivery(db, d.id)

        it.qty_received = round(recv_sum, 3)
        it.qty_remaining = round(qty_order - recv_sum, 3)
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


def create_po(db: Session, data: POCreate, user_id: int) -> PurchaseOrder:
    po = PurchaseOrder(
        code=data.code or "", misa_code=data.misa_code, pr_code=data.pr_code,
        survey_code=data.survey_code, company_id=data.company_id, supplier_code=data.supplier_code,
        supplier_name=data.supplier_name, department=data.department, nspt=data.nspt,
        order_date=data.order_date, vat_rate=data.vat_rate, is_urgent=data.is_urgent,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
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
    for k, v in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(po, k, v)
    po.updated_by = user_id
    _save_items(db, po, data.items, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    record(db, user_id, ENTITY, pid, "update")
    return po


def delete_po(db: Session, pid: int, user_id: int):
    po = get_po(db, pid)
    for it in items_of(db, pid):
        for d in deliveries_of(db, it.id):
            _cleanup_delivery(db, d.id)
            db.delete(d)
        db.delete(it)
    db.delete(po)
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseOrder:
    po = get_po(db, pid)
    po.status = status
    if message:
        po.approve_note = message
    po.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    db.refresh(po)
    return po
