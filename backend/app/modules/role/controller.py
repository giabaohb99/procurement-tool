from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters
from app.core.database import get_db
from app.core import privilege_escalation
from app.core.permissions import (ACTION_LABELS, ACTIONS, ENTITIES,
                                  ENTITY_LABELS, SCOPE_LABELS, SCOPES)
from app.core.response import success

from . import service
from .model import Role
from .schema import PermissionUpdate, RoleCreate, RoleOrder, RoleOut, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["role"])


@router.get("/meta")
def permission_meta(db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    """Danh sách quyền config (đối tượng x hành động) để FE dựng ma trận."""
    return success({
        "entities": [{"key": e, "label": ENTITY_LABELS.get(e, e)} for e in ENTITIES],
        "actions": [{"key": a, "label": ACTION_LABELS.get(a, a)} for a in ACTIONS],
        "scopes": [{"key": s, "label": SCOPE_LABELS.get(s, s)} for s in SCOPES],
    })


FILTERABLE = ["code", "name", "description"]


@router.get("")
def list_roles(request: Request, db: Session = Depends(get_db),
               user=Depends(require("role", "read"))):
    # Trả mảng thô (không phân trang) — CrudList tự sort/phân trang phía client.
    q = apply_filters(service.list_roles_query(db), Role, request, FILTERABLE)
    return success([RoleOut.model_validate(r).model_dump() for r in q.all()])


@router.post("")
def create_role(data: RoleCreate, db: Session = Depends(get_db), user=Depends(require("role", "create"))):
    obj = service.create_role(db, data, user.id)
    return success(RoleOut.model_validate(obj).model_dump(), "Đã tạo vai trò", 201)


@router.put("/order")
def sap_xep_vai_tro(
    data: RoleOrder, db: Session = Depends(get_db),
    user=Depends(require("role", "write")),
):
    """Lưu THỨ TỰ HIỆN của danh sách vai trò (kéo thả ở màn Phân quyền).

    ⚠️ Khai TRƯỚC mọi route `/{rid}` kẻo "order" bị đọc thành id vai trò.

    Không gác bằng `privilege_escalation`: đổi chỗ hai dòng trong danh sách
    không cấp thêm cho ai quyền gì — khác hẳn việc tick ô trong ma trận. Vẫn
    đòi `role.write` vì đây là thứ mọi người quản trị khác đều nhìn thấy.
    """
    service.sap_xep_vai_tro(db, data.role_ids, user.id)
    return success(None, "Đã lưu thứ tự vai trò")


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
        "can_cancel": p.can_cancel, "can_print": p.can_print, "can_export": p.can_export, "scope": p.scope,
    } for p in perms])


@router.put("/{rid}/permissions")
def set_permissions(
    rid: int, data: PermissionUpdate, db: Session = Depends(get_db),
    user=Depends(require("role", "write")),
):
    #  Cửa sau thứ ba của tự nâng quyền: không đụng tới tài khoản nào cả, chỉ
    #  tick thêm ô vào ma trận của CHÍNH vai trò mình đang giữ. Xem
    #  `core/privilege_escalation.py`.
    privilege_escalation.chan_sua_vai_tro_cua_chinh_minh(db, rid, user)
    privilege_escalation.chan_cap_vuot_quyen(
        db, user, privilege_escalation.quyen_trong_ma_tran(data.permissions))
    service.set_permissions(db, rid, data, user.id)
    return success(None, "Đã cập nhật phân quyền")
