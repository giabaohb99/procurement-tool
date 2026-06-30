"""Tồn kho: nhập từ phiếu nhận hàng (ngầm) + điều chỉnh tay. Phase 2 chỉ +nhập/điều chỉnh."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from .model import Inventory, InventoryMove

FILTERABLE = ["warehouse_code", "product_code", "product_name"]


def _recompute(db: Session, company_id: int, warehouse_code: str, product_code: str,
               product_name: str = "", unit: str = ""):
    """Tính lại tồn + giá BÌNH QUÂN GIA QUYỀN của (company, kho, sp).

    qty = Σ move.qty ; value = Σ (move.qty × move.unit_price) ; avg_cost = value / qty.
    """
    moves = db.query(InventoryMove).filter(
        InventoryMove.company_id == company_id,
        InventoryMove.warehouse_code == warehouse_code,
        InventoryMove.product_code == product_code,
    ).all()
    total = sum(float(m.qty or 0) for m in moves)
    value = sum(float(m.qty or 0) * float(m.unit_price or 0) for m in moves)
    row = db.query(Inventory).filter(
        Inventory.company_id == company_id,
        Inventory.warehouse_code == warehouse_code,
        Inventory.product_code == product_code,
    ).first()
    if not row:
        row = Inventory(company_id=company_id, warehouse_code=warehouse_code,
                        product_code=product_code, product_name=product_name, unit=unit)
        db.add(row)
    row.qty = round(total, 3)
    row.avg_cost = round(value / total, 2) if total else 0
    row.value = round(value, 2)
    if product_name:
        row.product_name = product_name
    if unit:
        row.unit = unit
    db.flush()
    return row


def apply_delivery(db: Session, *, delivery_id: int, company_id: int, warehouse_code: str,
                   product_code: str, product_name: str, unit: str, qty: float, price: float, user_id: int):
    """Upsert 1 phát sinh nhập kho cho 1 lần giao (idempotent theo delivery_id).

    Lưu cả đơn giá nhập để tính bình quân gia quyền. Tính lại tồn cho cả key cũ & mới.
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
    mv.unit_price = price
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
    """Điều chỉnh tay (qty có thể âm/dương). Dùng đơn giá = giá BQ hiện tại để không lệch trị giá."""
    cur = db.query(Inventory).filter(
        Inventory.company_id == company_id, Inventory.warehouse_code == warehouse_code,
        Inventory.product_code == product_code,
    ).first()
    price = float(cur.avg_cost or 0) if cur else 0
    db.add(InventoryMove(company_id=company_id, warehouse_code=warehouse_code,
                         product_code=product_code, qty=qty, unit_price=price, ref_type="adjust",
                         note=note, created_by=user_id, updated_by=user_id))
    db.flush()
    row = _recompute(db, company_id, warehouse_code, product_code, product_name, unit)
    db.commit()
    return row
