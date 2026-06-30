from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["company"])


@router.get("")
def list_companies(
    q: str | None = Query(None),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("company", "read")),
):
    total, items = service.list_companies(db, q, pg)
    return success({
        "total": total,
        "items": [CompanyOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{cid}")
def get_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "read"))):
    return success(CompanyOut.model_validate(service.get_company(db, cid)).model_dump())


@router.post("")
def create_company(
    data: CompanyCreate, db: Session = Depends(get_db), user=Depends(require("company", "create"))
):
    obj = service.create_company(db, data, user.id)
    return success(CompanyOut.model_validate(obj).model_dump(), "Đã tạo công ty", 201)


@router.patch("/{cid}")
def update_company(
    cid: int, data: CompanyUpdate, db: Session = Depends(get_db),
    user=Depends(require("company", "write")),
):
    obj = service.update_company(db, cid, data, user.id)
    return success(CompanyOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{cid}")
def delete_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "delete"))):
    service.delete_company(db, cid, user.id)
    return success(None, "Đã xóa")
