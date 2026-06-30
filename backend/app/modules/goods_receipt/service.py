"""GR ngầm: tạo/cập nhật phiếu nhập kho theo từng lần giao. Không có màn nhập riêng."""
from sqlalchemy.orm import Session

from .model import GoodsReceipt


def upsert_for_delivery(db: Session, *, po_id: int, po_code: str, delivery_id: int,
                        company_id: int, warehouse_code: str, product_code: str,
                        product_name: str, unit: str, qty_received: float,
                        received_date: str, qc_result: str, user_id: int):
    gr = db.query(GoodsReceipt).filter(GoodsReceipt.delivery_id == delivery_id).first()
    if not gr:
        gr = GoodsReceipt(delivery_id=delivery_id, created_by=user_id)
        db.add(gr)
        db.flush()
        gr.code = f"GR{gr.id:05d}"
    gr.po_id = po_id
    gr.po_code = po_code
    gr.company_id = company_id
    gr.warehouse_code = warehouse_code
    gr.product_code = product_code
    gr.product_name = product_name
    gr.unit = unit
    gr.qty_received = qty_received
    gr.received_date = received_date
    gr.qc_result = qc_result
    gr.updated_by = user_id
    db.flush()
    return gr


def remove_for_delivery(db: Session, delivery_id: int):
    gr = db.query(GoodsReceipt).filter(GoodsReceipt.delivery_id == delivery_id).first()
    if gr:
        db.delete(gr)
        db.flush()
