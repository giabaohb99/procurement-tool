from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Supplier
from .schema import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/api/suppliers", tags=["supplier"])


@router.get("")
def list_suppliers(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "read")),
):
    query = apply_filters(db.query(Supplier), Supplier, request, service.FILTERABLE)
    total, items = service.list_suppliers(db, query, pg)
    return success({
        "total": total,
        "items": [SupplierOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{sid}")
def get_supplier(sid: int, db: Session = Depends(get_db), user=Depends(require("supplier", "read"))):
    return success(SupplierOut.model_validate(service.get_supplier(db, sid)).model_dump())


@router.post("")
def create_supplier(
    data: SupplierCreate, db: Session = Depends(get_db),
    user=Depends(require("supplier", "create")),
):
    obj = service.create_supplier(db, data, user.id)
    return success(SupplierOut.model_validate(obj).model_dump(), "Đã tạo NCC", 201)


@router.patch("/{sid}")
def update_supplier(
    sid: int, data: SupplierUpdate, db: Session = Depends(get_db),
    user=Depends(require("supplier", "write")),
):
    obj = service.update_supplier(db, sid, data, user.id)
    return success(SupplierOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{sid}")
def delete_supplier(
    sid: int, db: Session = Depends(get_db), user=Depends(require("supplier", "delete"))
):
    service.delete_supplier(db, sid, user.id)
    return success(None, "Đã xóa")
