"""Tồn kho: nhập từ phiếu nhận hàng (ngầm) + điều chỉnh tay. Phase 2 chỉ +nhập/điều chỉnh."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from .model import Inventory, InventoryMove

FILTERABLE = ["warehouse_code", "product_code", "product_name"]


def _recompute(db: Session, company_id: int, warehouse_code: str, product_code: str,
               product_name: str = "", unit: str = ""):
    """Tính lại tồn = tổng các phát sinh của (company, kho, sp)."""
    total = db.query(func.coalesce(func.sum(InventoryMove.qty), 0)).filter(
        InventoryMove.company_id == company_id,
        InventoryMove.warehouse_code == warehouse_code,
        InventoryMove.product_code == product_code,
    ).scalar() or 0
    row = db.query(Inventory).filter(
        Inventory.company_id == company_id,
        Inventory.warehouse_code == warehouse_code,
        Inventory.product_code == product_code,
    ).first()
    if not row:
        row = Inventory(company_id=company_id, warehouse_code=warehouse_code,
                        product_code=product_code, product_name=product_name, unit=unit)
        db.add(row)
    row.qty = total
    if product_name:
        row.product_name = product_name
    if unit:
        row.unit = unit
    db.flush()
    return row


def apply_delivery(db: Session, *, delivery_id: int, company_id: int, warehouse_code: str,
                   product_code: str, product_name: str, unit: str, qty: float, user_id: int):
    """Upsert 1 phát sinh nhập kho cho 1 lần giao (idempotent theo delivery_id).

    Sửa SL nhận / đổi kho đều cập nhật lại; tính lại tồn cho cả key cũ & mới.
    """
    mv = db.query(InventoryMove).filter(
        InventoryMove.ref_type == "gr", InventoryMove.ref_id == delivery_id
    ).first()
    old_key = (mv.company_id, mv.warehouse_code, mv.product_code) if mv else None
    if not mv:
        mv = InventoryMove(ref_type="gr", ref_id=delivery_id, created_by=user_id)
        db.add(mv)
    mv.company_id = company_id
    mv.warehouse_code = warehouse_code
    mv.product_code = product_code
    mv.qty = qty
    mv.updated_by = user_id
    mv.note = "Nhận hàng từ PO"
    db.flush()
    _recompute(db, company_id, warehouse_code, product_code, product_name, unit)
    if old_key and old_key != (company_id, warehouse_code, product_code):
        _recompute(db, *old_key)


def remove_delivery(db: Session, delivery_id: int):
    """Xóa phát sinh nhập kho của 1 lần giao (khi xóa dòng giao / SL nhận = 0)."""
    mv = db.query(InventoryMove).filter(
        InventoryMove.ref_type == "gr", InventoryMove.ref_id == delivery_id
    ).first()
    if not mv:
        return
    key = (mv.company_id, mv.warehouse_code, mv.product_code)
    db.delete(mv)
    db.flush()
    _recompute(db, *key)


def adjust(db: Session, *, company_id: int, warehouse_code: str, product_code: str,
           product_name: str, unit: str, qty: float, note: str, user_id: int):
    """Điều chỉnh tay (qty có thể âm/dương)."""
    db.add(InventoryMove(company_id=company_id, warehouse_code=warehouse_code,
                         product_code=product_code, qty=qty, ref_type="adjust",
                         note=note, created_by=user_id, updated_by=user_id))
    db.flush()
    row = _recompute(db, company_id, warehouse_code, product_code, product_name, unit)
    db.commit()
    return row
