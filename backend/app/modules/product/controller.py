from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Product
from .schema import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["product"])


@router.get("")
def list_products(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("product", "read")),
):
    query = apply_filters(db.query(Product), Product, request, service.FILTERABLE)
    total, items = service.list_products(db, query, pg)
    return success({
        "total": total,
        "items": [ProductOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{pid}")
def get_product(pid: int, db: Session = Depends(get_db), user=Depends(require("product", "read"))):
    return success(ProductOut.model_validate(service.get_product(db, pid)).model_dump())


@router.post("")
def create_product(
    data: ProductCreate, db: Session = Depends(get_db), user=Depends(require("product", "create"))
):
    obj = service.create_product(db, data, user.id)
    return success(ProductOut.model_validate(obj).model_dump(), "Đã tạo sản phẩm", 201)


@router.patch("/{pid}")
def update_product(
    pid: int, data: ProductUpdate, db: Session = Depends(get_db),
    user=Depends(require("product", "write")),
):
    obj = service.update_product(db, pid, data, user.id)
    return success(ProductOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{pid}")
def delete_product(
    pid: int, db: Session = Depends(get_db), user=Depends(require("product", "delete"))
):
    service.delete_product(db, pid, user.id)
    return success(None, "Đã xóa")
