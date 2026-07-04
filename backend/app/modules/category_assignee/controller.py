from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import CategoryAssigneeCreate, CategoryAssigneeOut, CategoryAssigneeUpdate

router = APIRouter(prefix="/api/category-assignees", tags=["category_assignee"])


def _out(db: Session, obj) -> dict:
    from app.modules.catalog.model import ItemGroup
    from app.modules.employee.model import Employee
    d = CategoryAssigneeOut.model_validate(obj).model_dump()
    g = db.get(ItemGroup, obj.item_group_id) if obj.item_group_id else None
    p = db.get(Employee, obj.primary_employee_id) if obj.primary_employee_id else None
    b = db.get(Employee, obj.backup_employee_id) if obj.backup_employee_id else None
    d["item_group_name"] = g.name if g else None
    d["primary_name"] = p.full_name if p else None
    d["backup_name"] = b.full_name if b else None
    return d


@router.get("")
def list_(db: Session = Depends(get_db), user=Depends(require("category_assignee", "read"))):
    items = [_out(db, o) for o in service.list_all(db)]
    return success({"total": len(items), "items": items})


@router.get("/{cid}")
def get_(cid: int, db: Session = Depends(get_db), user=Depends(require("category_assignee", "read"))):
    return success(_out(db, service.get(db, cid)))


@router.post("")
def create_(data: CategoryAssigneeCreate, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "create"))):
    return success(_out(db, service.create(db, data, user.id)), "Đã tạo phân công", 201)


@router.patch("/{cid}")
def update_(cid: int, data: CategoryAssigneeUpdate, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "write"))):
    return success(_out(db, service.update(db, cid, data, user.id)), "Đã cập nhật")


@router.delete("/{cid}")
def delete_(cid: int, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "delete"))):
    service.delete(db, cid, user.id)
    return success(None, "Đã xóa")
