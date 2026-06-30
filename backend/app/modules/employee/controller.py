from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employee"])


@router.get("")
def list_employees(
    q: str | None = Query(None),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    total, items = service.list_employees(db, q, pg)
    return success({
        "total": total,
        "items": [EmployeeOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{eid}")
def get_employee(eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    return success(EmployeeOut.model_validate(service.get_employee(db, eid)).model_dump())


@router.post("")
def create_employee(
    data: EmployeeCreate, db: Session = Depends(get_db),
    user=Depends(require("employee", "create")),
):
    obj = service.create_employee(db, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã tạo nhân viên", 201)


@router.patch("/{eid}")
def update_employee(
    eid: int, data: EmployeeUpdate, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    obj = service.update_employee(db, eid, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{eid}")
def delete_employee(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "delete"))
):
    service.delete_employee(db, eid, user.id)
    return success(None, "Đã xóa")
