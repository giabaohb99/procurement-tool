"""API Danh sách biến mẫu HĐLĐ — `/api/labor-contract-variables` (duoc-CR-630).

Không entity quyền mới: tái dùng `labor_contract_template` (read xem · write tạo/sửa · delete xóa), và
GHI còn đòi phạm vi "tất cả pháp nhân" (`variable_access`). Danh mục là toàn hệ thống nên KHÔNG `apply_scope`
lên bảng biến. `/input-fields` PHẢI khai TRƯỚC `/{variable_id}`.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import error, success

from . import variable_access, variable_serializer as ser, variable_service as svc
from .access import has_perm
from .variable_schema import VariableCreate, VariableUpdate

router = APIRouter(prefix="/api/labor-contract-variables", tags=["labor-contract-variable"])
ENTITY = variable_access.ENTITY
AUDIT_ENTITY = "labor_contract_variable"


def _one(db: Session, row) -> dict:
    return ser.serialize_variables(db, [row])[0]


@router.get("")
def list_variables(q: str = "", source: int | None = None, value_type: int | None = None,
                   is_active: bool | None = None, pg: dict = Depends(pagination),
                   db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    profile = get_perm_profile(db, user)
    total, rows = svc.list_variables(db, q=q, source=source, value_type=value_type, is_active=is_active,
                                     offset=pg["offset"], limit=pg["limit"])
    return success({"total": total, "items": ser.serialize_variables(db, rows),
                    "can_manage": variable_access.is_unrestricted(user, profile, "write"),
                    "can_delete": variable_access.is_unrestricted(user, profile, "delete")})


@router.get("/input-fields")
def input_fields(include_inactive: bool = False, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    profile = get_perm_profile(db, user)
    if not (has_perm(profile, ENTITY, "read") or has_perm(profile, "labor_contract", "create")
            or has_perm(profile, "labor_contract", "write")):
        raise HTTPException(403, "Không có quyền xem biến nhập của hợp đồng lao động")
    return success(ser.input_fields(db, include_inactive))


@router.get("/{variable_id}")
def get_variable(variable_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    row = svc.get_or_404(db, variable_id)
    info = svc.usage(db, user, get_perm_profile(db, user), row)
    return success({**_one(db, row), "usage": info, "code_locked": svc.code_locked(db, row)})


@router.post("")
def create_variable(data: VariableCreate, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    variable_access.ensure_unrestricted(user, get_perm_profile(db, user), "write")
    row = svc.create(db, user, data)
    audit_record(db, user.id, AUDIT_ENTITY, row.id, "create", f"Thêm biến mẫu hợp đồng lao động \"{row.code}\"")
    return success(_one(db, row), "Đã thêm biến", 201)


@router.patch("/{variable_id}")
def update_variable(variable_id: int, data: VariableUpdate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "write"))):
    variable_access.ensure_unrestricted(user, get_perm_profile(db, user), "write")
    row = svc.update(db, user, svc.get_or_404(db, variable_id, lock=True), data)
    audit_record(db, user.id, AUDIT_ENTITY, row.id, "update", f"Sửa biến mẫu hợp đồng lao động \"{row.code}\"")
    return success(_one(db, row), "Đã cập nhật biến")


@router.delete("/{variable_id}")
def delete_variable(variable_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    profile = get_perm_profile(db, user)
    variable_access.ensure_unrestricted(user, profile, "delete")
    row = svc.get_or_404(db, variable_id, lock=True)
    try:
        code = svc.delete(db, user, profile, row)
    except svc.VariableInUse as exc:
        return error(exc.message, code="409", status_code=409, details=exc.details)
    audit_record(db, user.id, AUDIT_ENTITY, variable_id, "delete", f"Xóa biến mẫu hợp đồng lao động \"{code}\"")
    return success(None, "Đã xóa biến")
