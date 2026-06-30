from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Inventory, InventoryMove
from .schema import AdjustIn

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _out(r: Inventory) -> dict:
    return {"id": r.id, "company_id": r.company_id, "warehouse_code": r.warehouse_code,
            "product_code": r.product_code, "product_name": r.product_name,
            "unit": r.unit, "qty": float(r.qty or 0),
            "avg_cost": float(r.avg_cost or 0), "value": float(r.value or 0)}


@router.get("")
def list_inventory(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                   user=Depends(require("inventory", "read"))):
    q = apply_filters(db.query(Inventory), Inventory, request, service.FILTERABLE)
    company_id = request.query_params.get("company_id")
    if company_id:
        q = q.filter(Inventory.company_id == int(company_id))
    total = q.count()
    items = q.order_by(Inventory.product_code.asc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_out(i) for i in items]})


@router.get("/moves")
def list_moves(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
               user=Depends(require("inventory", "read"))):
    q = db.query(InventoryMove)
    for k in ("warehouse_code", "product_code"):
        v = request.query_params.get(k)
        if v:
            q = q.filter(getattr(InventoryMove, k) == v)
    total = q.count()
    rows = q.order_by(InventoryMove.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    items = [{"id": m.id, "company_id": m.company_id, "warehouse_code": m.warehouse_code,
              "product_code": m.product_code, "qty": float(m.qty or 0), "ref_type": m.ref_type,
              "ref_id": m.ref_id, "note": m.note, "at": m.created_at} for m in rows]
    return success({"total": total, "items": items})


@router.post("/adjust")
def adjust(data: AdjustIn, db: Session = Depends(get_db), user=Depends(require("inventory", "write"))):
    row = service.adjust(db, company_id=data.company_id, warehouse_code=data.warehouse_code,
                         product_code=data.product_code, product_name=data.product_name,
                         unit=data.unit, qty=data.qty, note=data.note, user_id=user.id)
    record(db, user.id, "inventory", row.id, "adjust", data.note)
    return success(_out(row), "Đã điều chỉnh tồn kho")
