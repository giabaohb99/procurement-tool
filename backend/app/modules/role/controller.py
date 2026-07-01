from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.permissions import (ACTION_LABELS, ACTIONS, ENTITIES,
                                  ENTITY_LABELS, SCOPES)
from app.core.response import success

from . import service
from .schema import PermissionUpdate, RoleCreate, RoleOut, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["role"])


@router.get("/meta")
def permission_meta(db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    """Danh sách quyền config (đối tượng x hành động) để FE dựng ma trận."""
    return success({
        "entities": [{"key": e, "label": ENTITY_LABELS.get(e, e)} for e in ENTITIES],
        "actions": [{"key": a, "label": ACTION_LABELS.get(a, a)} for a in ACTIONS],
        "scopes": SCOPES,
    })


@router.get("")
def list_roles(db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    return success([RoleOut.model_validate(r).model_dump() for r in service.list_roles(db)])


@router.post("")
def create_role(data: RoleCreate, db: Session = Depends(get_db), user=Depends(require("role", "create"))):
    obj = service.create_role(db, data, user.id)
    return success(RoleOut.model_validate(obj).model_dump(), "Đã tạo vai trò", 201)


@router.get("/{rid}")
def get_role(rid: int, db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    obj = service.get_role(db, rid)
    return success(RoleOut.model_validate(obj).model_dump())


@router.patch("/{rid}")
def update_role(rid: int, data: RoleUpdate, db: Session = Depends(get_db), user=Depends(require("role", "write"))):
    obj = service.update_role(db, rid, data, user.id)
    return success(RoleOut.model_validate(obj).model_dump(), "Đã cập nhật vai trò")


@router.delete("/{rid}")
def delete_role(rid: int, db: Session = Depends(get_db), user=Depends(require("role", "delete"))):
    service.delete_role(db, rid, user.id)
    return success(None, "Đã xóa vai trò")


@router.get("/{rid}/permissions")
def get_permissions(rid: int, db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    perms = service.get_permissions(db, rid)
    return success([{
        "entity": p.entity, "can_read": p.can_read, "can_create": p.can_create,
        "can_write": p.can_write, "can_delete": p.can_delete, "can_approve": p.can_approve,
        "can_print": p.can_print, "can_export": p.can_export, "scope": p.scope,
    } for p in perms])


@router.put("/{rid}/permissions")
def set_permissions(
    rid: int, data: PermissionUpdate, db: Session = Depends(get_db),
    user=Depends(require("role", "write")),
):
    service.set_permissions(db, rid, data, user.id)
    return success(None, "Đã cập nhật phân quyền")
