from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/departments", tags=["department"])


@router.get("")
def list_departments(
    q: str | None = Query(None),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("department", "read")),
):
    total, items = service.list_departments(db, q, pg)
    return success({
        "total": total,
        "items": [DepartmentOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{did}")
def get_department(did: int, db: Session = Depends(get_db), user=Depends(require("department", "read"))):
    return success(DepartmentOut.model_validate(service.get_department(db, did)).model_dump())


@router.post("")
def create_department(
    data: DepartmentCreate, db: Session = Depends(get_db),
    user=Depends(require("department", "create")),
):
    obj = service.create_department(db, data, user.id)
    return success(DepartmentOut.model_validate(obj).model_dump(), "Đã tạo phòng ban", 201)


@router.patch("/{did}")
def update_department(
    did: int, data: DepartmentUpdate, db: Session = Depends(get_db),
    user=Depends(require("department", "write")),
):
    obj = service.update_department(db, did, data, user.id)
    return success(DepartmentOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{did}")
def delete_department(
    did: int, db: Session = Depends(get_db), user=Depends(require("department", "delete"))
):
    service.delete_department(db, did, user.id)
    return success(None, "Đã xóa")
